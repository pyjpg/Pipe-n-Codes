from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import uuid

# — Connect to your local Cassandra (127.0.0.1:9042 by default) —
cluster = Cluster(['127.0.0.1'], port=9042)
cass_session = cluster.connect()

# — Create / Ensure the keyspace & table exist —
cass_session.execute("""
    CREATE KEYSPACE IF NOT EXISTS rag_chat
    WITH replication = {
      'class': 'SimpleStrategy',
      'replication_factor': 1
    }
""")
cass_session.set_keyspace('rag_chat')
cass_session.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
      session_id text,
      ts         timeuuid,
      role       text,
      content    text,
      PRIMARY KEY ((session_id), ts)
    ) WITH CLUSTERING ORDER BY (ts DESC)
      AND default_time_to_live = 86400;
""")

print("✅ Connected to Cassandra and ensured `rag_chat.chat_history` exists.")
