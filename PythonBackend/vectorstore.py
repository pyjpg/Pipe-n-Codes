from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Use relative paths for better portability
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
VECTORSTORE_DIR = PROJECT_ROOT / "chroma_db"

def check_prerequisites():
    """Check if all required components are available"""
    print("🔍 Checking prerequisites...")
    
    if not COHERE_API_KEY:
        print("❌ COHERE_API_KEY not found in environment variables")
        return False
    
    if not DATA_DIR.exists():
        print(f"❌ Data directory not found: {DATA_DIR}")
        return False
    
    # Check if there are any files in data directory
    files = list(DATA_DIR.rglob("*"))
    data_files = [f for f in files if f.is_file()]
    
    if not data_files:
        print(f"❌ No files found in data directory: {DATA_DIR}")
        return False
    
    print(f"✅ Found {len(data_files)} files in data directory")
    print("✅ Prerequisites check passed")
    return True

def initialize_embeddings():
    """Initialize Cohere embeddings with error handling"""
    try:
        embd = CohereEmbeddings(
            model="embed-english-v3.0",
            cohere_api_key=COHERE_API_KEY,
        )
        print("✅ Cohere embeddings initialized")
        return embd
    except Exception as e:
        print(f"❌ Failed to initialize embeddings: {e}")
        return None

def load_documents():
    """Load both PDF and text documents from the data directory"""
    print(f"📂 Loading documents from {DATA_DIR}")
    all_docs = []
    
    # Load PDF documents
    try:
        pdf_loader = DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
        )
        pdf_docs = pdf_loader.load()
        all_docs.extend(pdf_docs)
        print(f"✅ Loaded {len(pdf_docs)} PDF documents")
    except Exception as e:
        print(f"⚠️  Could not load PDF documents: {e}")
    
    # Load text documents (.txt files)
    try:
        txt_loader = DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8", "errors": "ignore"}
        )
        txt_docs = txt_loader.load()
        all_docs.extend(txt_docs)
        print(f"✅ Loaded {len(txt_docs)} text documents")
    except Exception as e:
        print(f"⚠️  Could not load TXT documents: {e}")
    
    # Load any other text-based files
    try:
        general_loader = DirectoryLoader(
            str(DATA_DIR),
            glob="**/*",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8", "errors": "ignore"},
            silent_errors=True,
        )
        general_docs = general_loader.load()
        # Filter out duplicates (files already loaded as PDF/TXT)
        existing_sources = {doc.metadata.get('source') for doc in all_docs}
        new_docs = [doc for doc in general_docs if doc.metadata.get('source') not in existing_sources]
        all_docs.extend(new_docs)
        print(f"✅ Loaded {len(new_docs)} additional documents")
    except Exception as e:
        print(f"⚠️  Could not load additional documents: {e}")
    
    print(f"📊 Total documents loaded: {len(all_docs)}")
    
    # Print sample of loaded documents
    if all_docs:
        print("\n📄 Sample of loaded documents:")
        for i, doc in enumerate(all_docs[:3]):
            source = doc.metadata.get('source', 'Unknown')
            content_preview = doc.page_content[:100].replace('\n', ' ')
            print(f"  {i+1}. {Path(source).name}: {content_preview}...")
    
    return all_docs

def embed_documents_safely(docs, embeddings, batch_size=10):
    """
    Embed documents in batches with proper error handling and rate limiting.
    """
    print(f"🚀 Starting to embed {len(docs)} document chunks in batches of {batch_size}")
    
    vectorstore = None
    
    if VECTORSTORE_DIR.exists():
        print("📦 Loading existing vectorstore...")
        try:
            vectorstore = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
            
            # Check current count
            try:
                current_count = vectorstore._collection.count()
                print(f"📊 Current vectorstore contains {current_count} documents")
                
                # Ask user if they want to add more or recreate
                if current_count > 0:
                    print("🤔 Vectorstore already exists with documents.")
                    print("   Adding new documents to existing vectorstore...")
            except:
                print("⚠️  Could not check existing document count")
                
        except Exception as e:
            print(f"❌ Error loading existing vectorstore: {e}")
            print("🔄 Will create new vectorstore...")
            vectorstore = None
    
    # If no existing vectorstore or failed to load, create new one
    if vectorstore is None:
        print("🆕 Creating new vectorstore...")
        first_batch = docs[:batch_size]
        try:
            vectorstore = Chroma.from_documents(
                documents=first_batch,
                embedding=embeddings,
                persist_directory=str(VECTORSTORE_DIR),
            )
            print(f"✅ Created vectorstore with first batch of {len(first_batch)} documents")
            
            # Process remaining documents
            remaining_docs = docs[batch_size:]
        except Exception as e:
            print(f"❌ Error creating initial vectorstore: {e}")
            return None
    else:
        # Add all documents to existing vectorstore
        remaining_docs = docs
    
    # Add remaining documents in batches
    if remaining_docs:
        total_batches = (len(remaining_docs) + batch_size - 1) // batch_size
        
        for i in range(0, len(remaining_docs), batch_size):
            batch = remaining_docs[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"⏳ Processing batch {batch_num}/{total_batches} ({len(batch)} documents)...")
            
            try:
                vectorstore.add_documents(batch)
                print(f"✅ Added batch {batch_num}/{total_batches}")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"❌ Error adding batch {batch_num}: {e}")
                print("⏳ Sleeping 10 seconds before retry...")
                time.sleep(10)
                # Retry once
                try:
                    vectorstore.add_documents(batch)
                    print(f"✅ Successfully added batch {batch_num} on retry")
                except Exception as retry_error:
                    print(f"❌ Failed to add batch {batch_num} even on retry: {retry_error}")
                    continue
    
    return vectorstore

def test_vectorstore(vectorstore):
    """Test the vectorstore with sample queries"""
    print("\n🔍 Testing vectorstore with sample queries...")
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    test_queries = [
        "Building services docs 2010",
        "HVAC systems",
        "electrical systems",
        "fire safety",
        "plumbing systems"
    ]
    
    for query in test_queries:
        try:
            result = retriever.get_relevant_documents(query)
            print(f"  Query: '{query}' -> Retrieved {len(result)} documents")
            if result:
                content_preview = result[0].page_content[:100].replace('\n', ' ')
                print(f"    Sample: {content_preview}...")
        except Exception as e:
            print(f"    ❌ Error testing query '{query}': {e}")
    
    # Check total documents in vectorstore
    try:
        collection = vectorstore._collection
        total_count = collection.count()
        print(f"\n📊 Total documents in vectorstore: {total_count}")
        return total_count > 0
    except Exception as e:
        print(f"⚠️  Could not get document count: {e}")
        return False

def setup_vectorstore():
    """Main function to setup vectorstore - can be called from other modules"""
    print("🚀 Setting up vectorstore...")
    
    # Check prerequisites
    if not check_prerequisites():
        return False
    
    # Initialize embeddings
    embeddings = initialize_embeddings()
    if not embeddings:
        return False
    
    # Load documents
    docs = load_documents()
    if not docs:
        print("❌ No documents found! Check your data directory.")
        return False
    
    # Split docs into smaller chunks
    print("✂️  Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=256,
        chunk_overlap=0,
    )
    docs_split = text_splitter.split_documents(docs)
    print(f"📄 Split into {len(docs_split)} chunks")
    
    # Embed all documents
    vectorstore = embed_documents_safely(docs_split, embeddings, batch_size=10)
    
    if vectorstore:
        # Persist the vectorstore
        print("💾 Persisting vectorstore...")
        vectorstore.persist()
        print("✅ Successfully embedded all documents!")
        
        # Test the retrieval
        success = test_vectorstore(vectorstore)
        
        if success:
            print("\n🎉 Vectorstore setup completed successfully!")
            print("   Your RAG system should now be able to retrieve relevant documents.")
            return True
        else:
            print("\n⚠️  Vectorstore created but testing failed")
            return False
    else:
        print("❌ Failed to create vectorstore")
        return False

def check_vectorstore_exists():
    """Check if vectorstore already exists and has documents"""
    if not VECTORSTORE_DIR.exists():
        return False
    
    try:
        # Quick check without loading full vectorstore
        if not COHERE_API_KEY:
            return False
            
        embeddings = CohereEmbeddings(
            model="embed-english-v3.0",
            cohere_api_key=COHERE_API_KEY,
        )
        vectorstore = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
        count = vectorstore._collection.count()
        return count > 0
    except:
        return False

if __name__ == "__main__":
    # Run the setup when script is executed directly
    success = setup_vectorstore()
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)