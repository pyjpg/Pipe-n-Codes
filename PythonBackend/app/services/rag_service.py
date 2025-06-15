from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.schema import Document
from app.core.vectorstore import vector_store_manager
from app.core.llm import get_llm
from app.services.session_service import session_service
from app.services.grading_service import grading_service
from app.utils.prompts import SIMPLIFICATION_PROMPT, RAG_SYSTEM_PROMPT
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class RAGService:
    def __init__(self):
        self.llm = get_llm()
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup all the chains used in RAG"""
        # Simplifier chain
        simplify_prompt = ChatPromptTemplate.from_messages([
            ("human", SIMPLIFICATION_PROMPT)
        ])
        self.simplify_chain = simplify_prompt | self.llm | StrOutputParser()
        
        # RAG chain with conversation history
        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("system", "Retrieved chunks:\n{documents}\n"),
            ("human", "Question: {question}\nAnswer:")
        ])
        
        rag_chain = rag_prompt | self.llm | StrOutputParser()
        
        # Make it conversational
        self.conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: session_service.get_session_history_manager(session_id),
            input_messages_key="question",
            history_messages_key="chat_history",
        )
        
        # Fallback chain (without documents)
        fallback_prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Question: {question}\nAnswer:")
        ])
        
        fallback_chain = fallback_prompt | self.llm | StrOutputParser()
        
        self.conversational_fallback_chain = RunnableWithMessageHistory(
            fallback_chain,
            lambda session_id: session_service.get_session_history_manager(session_id),
            input_messages_key="question",
            history_messages_key="chat_history",
        )
    
    def retrieve(self, question: str, session_id: str = None) -> str:
        """Retrieve relevant documents from both chat history and main vectorstore"""
        try:
            # Search chat history vectorstore first
            chat_store = vector_store_manager.get_chat_store()
            chat_retriever = chat_store.as_retriever(search_kwargs={"k": 3})
            docs_chat = chat_retriever.get_relevant_documents(question)
            logger.info(f"Retrieved {len(docs_chat)} chat chunks for '{question}'")
            
            # Search main document vectorstore
            main_store = vector_store_manager.get_main_store()
            main_retriever = main_store.as_retriever(search_kwargs={"k": 3})
            docs_main = main_retriever.get_relevant_documents(question)
            logger.info(f"Retrieved {len(docs_main)} main chunks for '{question}'")
            
            # Combine results (chat chunks first for context)
            combined_docs = docs_chat + docs_main
            
            if not combined_docs:
                logger.warning(f"No relevant chunks found for: {question}")
                return ""
            
            # Join document contents
            docs_text = "\n\n".join(doc.page_content[:500] for doc in combined_docs)
            return docs_text
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return ""
    
    def process_question(self, question: str, session_id: str) -> Dict[str, Any]:
        """Main RAG pipeline processing"""
        logger.info(f"Processing question: {question} (session: {session_id})")
        
        # Step 1: Retrieve relevant documents
        documents = self.retrieve(question, session_id)
        logger.info(f"Retrieved {len(documents)} characters of context")
        
        # Step 2: Generate answer using RAG chain
        try:
            rag_response = self.conversational_rag_chain.invoke(
                {
                    "question": question,
                    "documents": documents
                },
                config={"configurable": {"session_id": session_id}}
            )
            logger.info("Generated RAG response")
        except Exception as e:
            logger.error(f"Error in RAG chain: {e}")
            rag_response = ""
        
        # Step 3: Check for hallucinations
        hallucination_score = "no"  # Default to no hallucination
        if documents and rag_response:
            try:
                hallucination_score = grading_service.check_hallucination(
                    documents=documents,
                    generation=rag_response
                )
                logger.info(f"Hallucination check: {hallucination_score}")
            except Exception as e:
                logger.error(f"Error checking hallucination: {e}")
        
        # Step 4: Use fallback if needed
        if hallucination_score == "yes" or not rag_response:
            logger.info("Using fallback due to hallucination or empty response")
            try:
                final_answer = self.conversational_fallback_chain.invoke(
                    {"question": question},
                    config={"configurable": {"session_id": session_id}}
                )
                source = "fallback"
            except Exception as e:
                logger.error(f"Error in fallback chain: {e}")
                final_answer = "I apologize, but I'm having trouble answering your question right now."
                source = "error"
        else:
            final_answer = rag_response
            source = "rag"
        
        # Step 5: Simplify for UI
        try:
            simplified_answer = self.simplify_chain.invoke({"answer": final_answer})
        except Exception as e:
            logger.error(f"Error simplifying answer: {e}")
            simplified_answer = final_answer
        
        # Save the conversation to chat history (embed for future retrieval)
        try:
            history_manager = session_service.get_session_history_manager(session_id)
            # The messages are automatically saved to Cassandra and embedded
            # through the CassandraChatMessageHistory class
        except Exception as e:
            logger.error(f"Error updating chat history: {e}")
        
        return {
            "answer": final_answer,
            "simplified_answer": simplified_answer,
            "source": source,
            "hallucination_score": hallucination_score,
            "retrieved_docs_length": len(documents),
            "session_id": session_id
        }
    
    def grade_document_relevance(self, question: str, document: str) -> str:
        """Grade if a document is relevant to the question"""
        return grading_service.grade_document_relevance(question, document)

# Singleton instance
rag_service = RAGService()