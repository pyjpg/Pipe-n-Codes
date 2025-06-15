from datetime import datetime
from typing import Dict, Any
from app.core.vectorstore import vector_store_manager
from app.core.database import cassandra_conn
from app.core.llm import get_llm
from app.services.rag_service import rag_service
import logging
import asyncio

logger = logging.getLogger(__name__)

class HealthService:
    async def check_vectorstore_health(self) -> Dict[str, Any]:
        """Check vectorstore health"""
        try:
            # Test retrieval
            documents = rag_service.retrieve("test query")
            
            main_exists = vector_store_manager.check_store_exists("main")
            chat_exists = vector_store_manager.check_store_exists("chat")
            
            return {
                "status": "healthy" if main_exists else "unhealthy",
                "main_store_exists": main_exists,
                "chat_store_exists": chat_exists,
                "can_retrieve": len(documents) >= 0,
                "message": "Vectorstore is working properly" if main_exists else "Vectorstore not found or empty"
            }
        except Exception as e:
            logger.error(f"Vectorstore health check failed: {e}")
            return {
                "status": "error",
                "main_store_exists": False,
                "chat_store_exists": False,
                "can_retrieve": False,
                "message": str(e)
            }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check Cassandra health"""
        try:
            session = cassandra_conn.get_session()
            # Simple query to test connection
            result = session.execute("SELECT now() FROM system.local")
            row = result.one()
            
            return {
                "status": "healthy",
                "connected": True,
                "server_time": str(row[0]) if row else None,
                "keyspace": session.keyspace,
                "message": "Database connection is healthy"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "error",
                "connected": False,
                "message": str(e)
            }
    
    async def check_llm_health(self) -> Dict[str, Any]:
        """Check LLM accessibility"""
        try:
            llm = get_llm()
            # Simple test query
            response = await asyncio.to_thread(
                llm.invoke, 
                "Reply with 'OK' if you receive this"
            )
            
            return {
                "status": "healthy",
                "accessible": True,
                "model": llm.model,
                "message": "LLM is accessible and responding"
            }
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return {
                "status": "error",
                "accessible": False,
                "message": str(e)
            }
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        vectorstore_health = await self.check_vectorstore_health()
        database_health = self.check_database_health()
        llm_health = await self.check_llm_health()
        
        # Overall status
        all_healthy = all([
            vectorstore_health["status"] == "healthy",
            database_health["status"] == "healthy",
            llm_health["status"] == "healthy"
        ])
        
        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "vectorstore": vectorstore_health,
                "database": database_health,
                "llm": llm_health
            },
            "ready_for_requests": all_healthy
        }

# Singleton instance
health_service = HealthService()