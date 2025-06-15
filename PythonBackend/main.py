import argparse
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logic 
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
from fastapi.middleware.cors import CORSMiddleware
from models.memory import MemoryData
from models.question import QuestionRequest
import vectorstore as vs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "https://assets.publishing.service.gov.uk",
    "https://www.gov.uk",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all origins, but be careful in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise EnvironmentError("COHERE_API_KEY must be set")

embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)

# Persist directory for vectorstore
VECTORSTORE_DIR = "./chroma_db"

# Setup text splitter
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=256,
    chunk_overlap=0,
)


@app.get("/debug/vectorstore")
def debug_vectorstore():
    try:
        vectorstore = Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=embeddings)
        # Get collection info
        collection = vectorstore._collection
        count = collection.count()
        return {"document_count": count, "vectorstore_exists": True}
    except Exception as e:
        return {"error": str(e), "vectorstore_exists": False}
@app.post("/memory/save")
async def save_memory(data: MemoryData):
    try:
        # Create a single Document from the memory data
        full_text = f"Title: {data.title}\nURL: {data.url}\n\n{data.bodyText}"
        doc = Document(page_content=full_text, metadata={"source": data.url})

        # Split into chunks
        docs_split = text_splitter.split_documents([doc])

        # Load or create vectorstore
        if os.path.exists(VECTORSTORE_DIR):
            vectorstore = Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=embeddings)
        else:
            vectorstore = Chroma.from_documents(docs_split, embedding=embeddings, persist_directory=VECTORSTORE_DIR)

        # Add new docs embeddings to vectorstore
        vectorstore.add_documents(docs_split)

        # Persist the updated vectorstore
        vectorstore.persist()

        return {"status": "success", "message": "Memory saved and embedded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag")
def rag_answer(req: QuestionRequest):
    try:
        # Step 1: Retrieve relevant documents
        documents = logic.retrieve(req.question, req.session_id)
        print(f"DEBUG: Retrieved {len(documents)} documents")
        # Step 2: Run conversational RAG pipeline with session management
        result = logic.run_conversational_rag(
            question=req.question,
            documents=documents,
            session_id=req.session_id
        )
        print(result)  # Debugging line to check the result

        return {
            "answer": result["simplified_answer"],
            "raw_answer": result["answer"],
            "source": result["source"],
            "hallucinated": (result["hallucination_score"] == "yes"),
            "session_id": req.session_id,
            "documents_used": result["documents_used"]
        }

    except Exception as e:
        logger.error(f"Error in /rag endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- New Session Management Endpoints ---
@app.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = logic.get_session_history(session_id)
        return {
            "session_id": session_id,
            "history": [{"type": msg.type, "content": msg.content} for msg in history]
        }
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear conversation history for a session"""
    try:
        logic.clear_conversation_history(session_id)
        return {"status": "success", "message": f"Session {session_id} cleared"}
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.on_event("startup")
async def startup_event():
    """Initialize vectorstore on application startup"""
    print("🚀 Starting up RAG application...")
    
    # Check if vectorstore already exists
    if vs.check_vectorstore_exists():
        print("✅ Vectorstore already exists and has documents")
        print("📊 Skipping embedding process...")
    else:
        print("🔄 Vectorstore not found or empty. Setting up embeddings...")
        success = vs.setup_vectorstore()
        
        if not success:
            print("❌ Failed to setup vectorstore on startup!")
            print("⚠️  Application will continue but RAG functionality may be limited")
        else:
            print("✅ Vectorstore setup completed on startup!")
    
    print("🎉 RAG application startup completed!")

# Also add a health check endpoint to verify vectorstore status
@app.get("/health/vectorstore")
def check_vectorstore_health():
    """Check if vectorstore is working properly"""
    try:
        # Quick test of vectorstore functionality
        documents = logic.retrieve("test query")
        
        if vs.check_vectorstore_exists():
            return {
                "status": "healthy",
                "vectorstore_exists": True,
                "can_retrieve": len(documents) >= 0,
                "message": "Vectorstore is working properly"
            }
        else:
            return {
                "status": "unhealthy", 
                "vectorstore_exists": False,
                "can_retrieve": False,
                "message": "Vectorstore not found or empty"
            }
    except Exception as e:
        return {
            "status": "error",
            "vectorstore_exists": False,
            "can_retrieve": False,
            "message": f"Error checking vectorstore: {str(e)}"
        }

# Add an endpoint to manually trigger embedding if needed
@app.post("/admin/rebuild_vectorstore")
def rebuild_vectorstore():
    """Manually rebuild the vectorstore (admin endpoint)"""
    try:
        print("🔄 Manually rebuilding vectorstore...")
        success = vs.setup_vectorstore()
        
        if success:
            return {
                "status": "success",
                "message": "Vectorstore rebuilt successfully"
            }
        else:
            return {
                "status": "error", 
                "message": "Failed to rebuild vectorstore"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error rebuilding vectorstore: {str(e)}"
        }
@app.get("/sessions")
def list_sessions():
    """List all active session IDs"""
    try:
        sessions = logic.list_active_sessions()
        return {"active_sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def main():
    parser = argparse.ArgumentParser(description="Run the RAG API")
    parser.add_argument("--serve", action="store_true", help="Start FastAPI server")
    args = parser.parse_args()

    if args.serve:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Please specify --serve to start the API server")

if __name__ == "__main__":
    main()