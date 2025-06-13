# models/cassandra_history.py

import os
from typing import List
from uuid import uuid4

from cassandra.query import SimpleStatement
from langchain_cohere import CohereEmbeddings
from langchain.schema import Document as LCDocument
from langchain_community.vectorstores import Chroma
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage  # make sure these match your langchain_core version


class CassandraChatMessageHistory(BaseChatMessageHistory):
    """
    A ChatMessageHistory implementation that writes/reads each message to/from Cassandra,
    and also embeds each message into a dedicated Chroma vectorstore for retrieval.
    """

    def __init__(self, cass_session, table_name: str, session_id: str, message_limit: int = 10):
        """
        cass_session: a connected Cassandra session object
        table_name: Cassandra table name, e.g. "chat_history"
        session_id: arbitrary string to group messages for one conversation
        message_limit: how many of the most recent rows to fetch each time .messages is called
        """
        self._cass = cass_session
        self._table = table_name
        self.session_id = session_id
        self._limit = message_limit

        # Initialize embeddings with Cohere
        self._emb = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=os.getenv("COHERE_API_KEY"))

        # Initialize (or load) Chroma vectorstore for chat embeddings
        self._chat_vs = Chroma(
            persist_directory="./chroma_chat_db",  # keep in sync with your logic.py
            embedding_function=self._emb
        )

        # Prepare Cassandra CQL statements once
        self._insert_stmt = self._cass.prepare(
            f"INSERT INTO {self._table} (session_id, ts, role, content) VALUES (?, now(), ?, ?);"
        )
        self._select_stmt = self._cass.prepare(
            f"SELECT ts, role, content FROM {self._table} WHERE session_id = ? LIMIT ?;"
        )

    def add_message(self, message) -> None:
        """
        Add a message to Cassandra and also embed it into the chat vectorstore.
        Supports HumanMessage and AIMessage.
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
        """
        # Insert into Cassandra
        self._cass.execute(self._insert_stmt, (self.session_id, "user", content))

        # Embed and add to Chroma vectorstore
        message_id = uuid4()
        doc = LCDocument(page_content=content, metadata={
            "session_id": self.session_id,
            "role": "user",
            "message_id": str(message_id)
        })
        self._chat_vs.add_documents([doc])
        self._chat_vs.persist()

    def add_ai_message(self, content: str) -> None:
        """
        Write a new 'assistant' message into Cassandra and embed into vectorstore.
        """
        # Insert into Cassandra
        self._cass.execute(self._insert_stmt, (self.session_id, "assistant", content))

        # Embed and add to Chroma vectorstore
        message_id = uuid4()
        doc = LCDocument(page_content=content, metadata={
            "session_id": self.session_id,
            "role": "assistant",
            "message_id": str(message_id)
        })
        self._chat_vs.add_documents([doc])
        self._chat_vs.persist()

    @property
    def messages(self) -> List:
        """
        Fetch the most recent `message_limit` messages from Cassandra,
        returning as a list of HumanMessage or AIMessage ordered oldest→newest.
        """
        rows = self._cass.execute(self._select_stmt, (self.session_id, self._limit))
        msgs = []
        # Cassandra rows are clustered DESC on ts, reverse to get chronological order
        for row in reversed(list(rows)):
            if row.role == "user":
                msgs.append(HumanMessage(content=row.content))
            else:
                msgs.append(AIMessage(content=row.content))
        return msgs

    def clear(self) -> None:
        """
        Delete all messages for this session_id from Cassandra.
        WARNING: This deletes the full conversation partition.
        """
        self._cass.execute(
            SimpleStatement(f"DELETE FROM {self._table} WHERE session_id = %s;"),
            (self.session_id,)
        )
        # Optionally clear embedded vectors? Not implemented here.
