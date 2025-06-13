from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_cohere import ChatCohere
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
from cassandra.cluster import Cluster
from models.cassandra_history import CassandraChatMessageHistory
import os
from dotenv import load_dotenv

load_dotenv()

#---- Set API keys 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)
PDF_VS_DIR = "./chroma_pdf_db"
CHAT_VS_DIR = "./chroma_chat_db"

# Initialize (or create if not exist) the PDF vectorstore:
pdf_vectorstore = Chroma(
    persist_directory=PDF_VS_DIR,
    embedding_function=embeddings
)

# Initialize (or create) the Chat‐History vectorstore:
chat_vectorstore = Chroma(
    persist_directory=CHAT_VS_DIR,
    embedding_function=embeddings
)

# Connect to Cassandra (unchanged)
cluster = Cluster(['127.0.0.1'], port=9042)
cass_session = cluster.connect()
cass_session.set_keyspace('rag_chat')
_history_store = {}
#connect to cassandra
try:
    cluster = Cluster(['127.0.0.1'], port=9042)
    cass_session = cluster.connect()
    cass_session.set_keyspace('rag_chat')
except Exception as e:
    raise RuntimeError(f"Failed to connect to Cassandra: {e}")

_history_store = {}

def get_session_history(session_id: str) -> CassandraChatMessageHistory:
    """
    Return a CassandraChatMessageHistory for this session_id.
    We only store up to `message_limit`=10 by default; you can override if desired.
    """
    if session_id not in _history_store:
        _history_store[session_id] = CassandraChatMessageHistory(
            cass_session=cass_session,
            table_name="chat_history",
            session_id=session_id,
            message_limit=10  # fetch last 10 messages each time .messages is accessed
        )
    return _history_store[session_id]

# --- Vector Store Setup ---
embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)
VECTORSTORE_DIR = "./chroma_db"

def retrieve(question: str, session_id: str) -> str:
    # 1) First search the chat_history vectorstore
    #    (so that if “Regulation 44” appeared in a prior assistant reply, it’s found here)
    chat_retriever = chat_vectorstore.as_retriever(search_kwargs={"k": 3})
    docs_chat = chat_retriever.get_relevant_documents(question)
    print(f"DEBUG: Retrieved {len(docs_chat)} chat chunks for '{question}'")

    # 2) Then search the PDF vectorstore
    #    We might still want PDF context if the chat story isn’t sufficient.
    pdf_retriever = pdf_vectorstore.as_retriever(search_kwargs={"k": 3})
    docs_pdf = pdf_retriever.get_relevant_documents(question)
    print(f"DEBUG: Retrieved {len(docs_pdf)} PDF chunks for '{question}'")

    # 3) Combine them, putting chat chunks first
    combined = docs_chat + docs_pdf
    if not combined:
        print("⚠️  No relevant chunks found in chat or PDFs for:", question)

    # 4) Join them into a single prompt string (e.g., take up to 500 chars each)
    docs_text = "\n\n".join(doc.page_content[:500] for doc in combined)
    return docs_text
# --- Fallback Chain ---
llm = ChatCohere(model="command-r", temperature=0)
llm_fallback_chain = (
    ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "Question: {question} \nAnswer:")
    ]) | llm | StrOutputParser()
)

# Make fallback chain conversational
conversational_fallback_chain = RunnableWithMessageHistory(
    llm_fallback_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

def fallback(question: str, session_id: str = "default"):
    """Fallback function that uses conversational chain"""
    return conversational_fallback_chain.invoke(
        {"question": question},
        config={"configurable": {"session_id": session_id}}
    )

# --- Simplifier Chain ---
simplifier_llm = ChatCohere(model="command-r", temperature=0)

simplify_prompt = ChatPromptTemplate.from_messages([
    (
        "human",
        """You are an assistant that rewrites long legal/technical answers to be clear, friendly, and ready to show on a modern web UI.

Instructions:
- Use a numbered list (1., 2., 3., etc.) to organize points.
- For each item, use a different emoji chosen from ✅, 🔹, ⭐, 🔸, 🛠️, cycling through them.
- Format important keywords in **bold** using Markdown.
- Be concise, remove fluff and redundancy.
- Use a warm and helpful tone.
- Output in Markdown format, ready for rendering.

Original Answer:
{answer}

Simplified and Engaging Markdown:"""
    )
])

simplify_chain = simplify_prompt | simplifier_llm | StrOutputParser()

def simplify(answer: str) -> str:
    """Simplify answer for UI display"""
    return simplify_chain.invoke({"answer": answer})

# --- RAG Chain ---
rag_llm = ChatCohere(model="command-r", temperature=0).bind(
    preamble="You are an assistant for question-answering tasks using retrieved context and conversation history."
)

rag_chain = ChatPromptTemplate.from_messages([
    ("system", "Below is the conversation so far and some retrieved context. Answer the question using both."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("system", "Retrieved chunks (chat or PDF):\n{documents}\n"),
    HumanMessagePromptTemplate.from_template("Question: {question}\nAnswer:")
]) | rag_llm | StrOutputParser()


# Make RAG chain conversational
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

def generate(question: str, documents: str, session_id: str = "default") -> str:
    """Generate answer using conversational RAG"""
    return conversational_rag_chain.invoke(
        {
            "question": question,
            "documents": documents
        },
        config={"configurable": {"session_id": session_id}}
    )

# --- Hallucination Grading Chain ---
class HallucinationScore(BaseModel):
    """Binary score to assess if an answer is grounded in the documents."""
    binary_score: Literal["yes", "no"] = Field(description="Answer must be 'yes' or 'no'.")

hallucination_preamble = """
You are a grader evaluating whether the generated answer is grounded in the provided documents.
If the answer can be verified using the documents, return "yes".
If the answer contains any hallucinations (information not found in the documents), return "no".
You must return exactly one of these two values: "yes" or "no".
"""

hallucination_llm = ChatCohere(model="command-r", temperature=0)
hallucination_grader = hallucination_llm.with_structured_output(
    HallucinationScore, preamble=hallucination_preamble
)

hallucination_prompt = ChatPromptTemplate.from_messages([
    ("human", "Documents:\n\n{documents}\n\nGenerated answer:\n\n{generation}")
])

hallucination_check_chain = hallucination_prompt | hallucination_grader

def check_hallucination(question: str, documents: str, answer: str) -> str:
    """Check if answer is hallucinated"""
    result = hallucination_check_chain.invoke({
        "documents": documents,
        "generation": answer
    })
    return result.binary_score

def get_session_history_messages(session_id: str):
    if session_id in _history_store:
        return _history_store[session_id].messages
    return []

def clear_conversation_history(session_id: str):
    """Clear the conversation history for a session."""
    if session_id in _history_store:
        _history_store[session_id].clear()

def list_active_sessions():
    """Get list of active session IDs."""
    return list(_history_store.keys())

# --- Main Pipeline Function ---
def run_conversational_rag(question: str, documents: str, session_id: str):
    """Main function to run the conversational RAG pipeline with debug logging"""
    
    print(f"=== DEBUG: Processing question: {question}")
    print(f"=== DEBUG: Documents length: {len(documents)} characters")
    print(f"=== DEBUG: Documents preview: {documents[:200]}...")
    
    # Step 1: Try RAG with conversation history
    rag_response = conversational_rag_chain.invoke(
        {
            "question": question,
            "documents": documents
        },
        config={"configurable": {"session_id": session_id}}
    )
    
    print(f"=== DEBUG: RAG Response: {rag_response}")
    
    # Step 2: Check for hallucinations
    hallucination_result = hallucination_check_chain.invoke({
        "documents": documents,
        "generation": rag_response
    })
    
    print(f"=== DEBUG: Hallucination score: {hallucination_result.binary_score}")
    
    # Step 3: Use fallback if hallucination detected
    if hallucination_result.binary_score == "no":
        print("=== DEBUG: Using RAG response")
        final_answer = rag_response
        source = "rag"
    else:
        print("=== DEBUG: Using fallback due to hallucination detection")
        final_answer = conversational_fallback_chain.invoke(
            {"question": question},
            config={"configurable": {"session_id": session_id}}
        )
        source = "fallback"
        
    
    # Step 4: Simplify for UI
    simplified_answer = simplify_chain.invoke({"answer": final_answer})
    
    return {
        "answer": final_answer,
        "simplified_answer": simplified_answer,
        "source": source,
        "hallucination_score": hallucination_result.binary_score,
        "retrieved_docs_length": len(documents),  # Add debug info
        "rag_response": rag_response if source == "fallback" else None  # Include original RAG response when fallback is used
    }