from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import time
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CassandraConnection:
    def __init__(self):
        self.cluster = None
        self.session = None
        self._connected = False
    
    def connect(self, max_retries: int = 5):
        """Connect to Cassandra with retry logic"""
        for attempt in range(max_retries):
            try:
                self.cluster = Cluster(
                    [settings.cassandra_host], 
                    port=settings.cassandra_port
                )
                self.session = self.cluster.connect()
                self._connected = True
                logger.info("✅ Connected to Cassandra!")
                self._setup_keyspace_and_table()
                return self.session
            except Exception as e:
                logger.warning(
                    f"Cassandra not ready, waiting 10 seconds... "
                    f"(attempt {attempt+1}/{max_retries})"
                )
                time.sleep(10)
        
        raise RuntimeError(
            f"Failed to connect to Cassandra after {max_retries} attempts!"
        )
    
    def _setup_keyspace_and_table(self):
        """Create keyspace and table if they don't exist"""
        # Create keyspace
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {settings.cassandra_keyspace}
            WITH replication = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
        """)
        logger.info(f"✅ Keyspace '{settings.cassandra_keyspace}' created/verified")
        
        # Use keyspace
        self.session.set_keyspace(settings.cassandra_keyspace)
        
        # Create table
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                session_id text,
                ts         timeuuid,
                role       text,
                content    text,
                PRIMARY KEY ((session_id), ts)
            ) WITH CLUSTERING ORDER BY (ts DESC)
              AND default_time_to_live = 86400;
        """)
        logger.info("✅ Table 'chat_history' created/verified")
    
    def get_session(self):
        if not self._connected:
            self.connect()
        return self.session
    
    def close(self):
        if self.cluster:
            self.cluster.shutdown()

# Singleton instance
cassandra_conn = CassandraConnection()