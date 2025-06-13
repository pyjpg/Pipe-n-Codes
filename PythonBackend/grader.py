from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere import ChatCohere
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Create the embeddings and vectorstore retriever
embd = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)

# Here you need your documents (docs_split), make sure docs_split is defined correctly
# Example placeholder:
docs_split = [...]  # Your preprocessed & split documents here

vectorstore = Chroma.from_documents(documents=docs_split, embedding=embd)
retriever = vectorstore.as_retriever()

class GradeDocuments(BaseModel):
    binary_score: Literal["yes", "no"] = Field(description="Answer must be 'yes' or 'no'.")

preamble = """You are a grader assessing the relevance of a retrieved document to a user's question.
If the document clearly or partially answers or relates to the question, return: "yes".
This includes direct answers, supporting information, or contextually useful content.
Only return "no" if the document is entirely unrelated or irrelevant to the question.
You must return exactly one of these two values: "yes" or "no".
"""



llm = ChatCohere(model="command-r", temperature=0, cohere_api_key=COHERE_API_KEY)
structured_llm_grader = llm.with_structured_output(GradeDocuments, preamble=preamble)

grade_prompt = ChatPromptTemplate.from_messages([
    ("human", "Retrieved document: \n\n{document}\n\nUser question: {question}")
])

retrieval_grader = grade_prompt | structured_llm_grader

# Now use your retriever to get docs for the question
docs = retriever.invoke("types of agent memory")
doc_txt = docs[0].page_content

response = retrieval_grader.invoke({"question": "types of agent memory", "document": doc_txt})
print(response)
