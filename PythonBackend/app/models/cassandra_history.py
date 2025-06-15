import os
from typing import List
from uuid import uuid4
from cassandra.query import SimpleStatement
from langchain_cohere import CohereEmbeddings
from langchain.schema import Document as LCDocument
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.core.vectorstore import vector_store_manager
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class CassandraChatMessageHistory(BaseChatMessageHistory):
    """
    A ChatMessageHistory implementation that writes/reads each message to/from Cassandra,
    and also embeds each message into a dedicated Chroma vectorstore for retrieval.
    """

    def __init__(
        self, 
        cass_session, 
        table_name: str, 
        session_id: str, 
        message_limit: int = 10
    ):
        """
        Initialize Cassandra chat message history.
        
        Args:
            cass_session: Connected Cassandra session object
            table_name: Cassandra table name (e.g., "chat_history")
            session_id: Unique identifier for conversation session
            message_limit: Maximum number of recent messages to fetch
        """
        self._cass = cass_session
        self._table = table_name
        self.session_id = session_id
        self._limit = message_limit

        # Get chat vectorstore from manager
        self._chat_vs = vector_store_manager.get_chat_store()

        # Prepare Cassandra CQL statements
        self._prepare_statements()

    def _prepare_statements(self):
        """Prepare CQL statements for better performance"""
        try:
            self._insert_stmt = self._cass.prepare(
                f"INSERT INTO {self._table} (session_id, ts, role, content) "
                f"VALUES (?, now(), ?, ?);"
            )
            self._select_stmt = self._cass.prepare(
                f"SELECT ts, role, content FROM {self._table} "
                f"WHERE session_id = ? LIMIT ?;"
            )
            self._delete_stmt = self._cass.prepare(
                f"DELETE FROM {self._table} WHERE session_id = ?;"
            )
        except Exception as e:
            logger.error(f"Error preparing statements: {e}")
            raise

    def add_message(self, message: BaseMessage) -> None:
        """
        Add a message to Cassandra and embed it into the chat vectorstore.
        
        Args:
            message: HumanMessage or AIMessage to add
        """
        if isinstance(message, HumanMessage):
            self.add_user_message(message.content)
        elif isinstance(message, AIMessage):
            self.add_ai_message(message.content)
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")

    def add_user_message(self, content: str) -> None:
        """
        Write a new 'user' message into Cassandra and embed into vectorstore.
        
        Args:
            content: The user's message content
        """
        try:
            # Insert into Cassandra
            self._cass.execute(
                self._insert_stmt, 
                (self.session_id, "user", content)
            )
            logger.debug(f"Added user message to Cassandra for session {self.session_id}")

            # Embed and add to Chroma vectorstore
            self._embed_message(content, "user")
            
        except Exception as e:
            logger.error(f"Error adding user message: {e}")
            raise

    def add_ai_message(self, content: str) -> None:
        """
        Write a new 'assistant' message into Cassandra and embed into vectorstore.
        
        Args:
            content: The assistant's message content
        """
        try:
            # Insert into Cassandra
            self._cass.execute(
                self._insert_stmt, 
                (self.session_id, "assistant", content)
            )
            logger.debug(f"Added AI message to Cassandra for session {self.session_id}")

            # Embed and add to Chroma vectorstore
            self._embed_message(content, "assistant")
            
        except Exception as e:
            logger.error(f"Error adding AI message: {e}")
            raise

    def _embed_message(self, content: str, role: str) -> None:
        """
        Embed a message and add it to the chat vectorstore.
        
        Args:
            content: Message content to embed
            role: Role of the message sender ('user' or 'assistant')
        """
        try:
            message_id = str(uuid4())
            
            # Create document with metadata
            doc = LCDocument(
                page_content=content,
                metadata={
                    "session_id": self.session_id,
                    "role": role,
                    "message_id": message_id,
                    "type": "chat_message"
                }
            )
            
            # Add to vectorstore
            self._chat_vs.add_documents([doc])
            self._chat_vs.persist()
            
            logger.debug(f"Embedded {role} message for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error embedding message: {e}")
            # Don't raise here - embedding failure shouldn't break chat

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Fetch the most recent messages from Cassandra.
        
        Returns:
            List of HumanMessage or AIMessage objects ordered oldest to newest
        """
        try:
            rows = self._cass.execute(
                self._select_stmt, 
                (self.session_id, self._limit)
            )
            
            msgs = []
            # Cassandra returns rows in DESC order, reverse for chronological
            for row in reversed(list(rows)):
                if row.role == "user":
                    msgs.append(HumanMessage(content=row.content))
                elif row.role == "assistant":
                    msgs.append(AIMessage(content=row.content))
                else:
                    logger.warning(f"Unknown role in message: {row.role}")
                    
            logger.debug(f"Retrieved {len(msgs)} messages for session {self.session_id}")
            return msgs
            
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return []

    def clear(self) -> None:
        """
        Delete all messages for this session from Cassandra.
        
        WARNING: This deletes the full conversation partition and cannot be undone.
        """
        try:
            self._cass.execute(self._delete_stmt, (self.session_id,))
            logger.info(f"Cleared all messages for session {self.session_id}")
            
            # Note: We don't clear embedded vectors as they might be useful
            # for cross-session context. Consider adding this if needed.
            
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            raise

    def get_message_count(self) -> int:
        """
        Get the total number of messages in this session.
        
        Returns:
            Number of messages in the session
        """
        try:
            result = self._cass.execute(
                f"SELECT COUNT(*) FROM {self._table} WHERE session_id = %s",
                (self.session_id,)
            )
            count = result.one()[0]
            return count
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0

    def get_session_summary(self) -> dict:
        """
        Get a summary of the session.
        
        Returns:
            Dictionary with session information
        """
        try:
            messages = self.messages
            user_messages = [m for m in messages if isinstance(m, HumanMessage)]
            ai_messages = [m for m in messages if isinstance(m, AIMessage)]
            
            return {
                "session_id": self.session_id,
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "ai_messages": len(ai_messages),
                "message_limit": self._limit
            }
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return {
                "session_id": self.session_id,
                "error": str(e)
            }