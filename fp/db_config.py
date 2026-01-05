# db_config.py - Correct Neo4j Aura connection
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv('.env-local')

class Neo4jConnection:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.driver = None
        
        if not self.uri or not self.user or not self.password:
            raise ValueError("Neo4j credentials not found in .env-local")
        
        self._connect()
    
    def _connect(self):
        """
        Connect to Neo4j Aura
        
        IMPORTANT: For neo4j+s:// and bolt+s:// URIs, 
        DO NOT use encrypted=True or trust parameters.
        The +s suffix handles encryption automatically.
        """
        
        try:
            print(f"🔌 Connecting to Neo4j Aura: {self.uri}")
            
            # ✅ CORRECT: For neo4j+s:// URIs, just use basic auth
            # No encrypted=True, no trust= parameters needed!
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"✅ Neo4j Aura connected successfully!")
            
            # Test with a simple query
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record['test'] == 1:
                    print(f"✅ Query test passed")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Connection failed: {error_msg}")
            
            # Provide helpful error messages
            if "authentication" in error_msg.lower():
                raise ConnectionError(
                    "Authentication failed. Please check NEO4J_USER and NEO4J_PASSWORD in .env-local"
                )
            elif "routing" in error_msg.lower():
                raise ConnectionError(
                    "Routing information unavailable. This might mean:\n"
                    "  1. Your IP is not whitelisted in Neo4j Aura\n"
                    "  2. The Neo4j instance is paused or stopped\n"
                    "  3. Network/firewall is blocking the connection\n\n"
                    "Please check: https://console.neo4j.io"
                )
            else:
                raise ConnectionError(f"Failed to connect to Neo4j: {error_msg}")
    
    def close(self):
        if self.driver:
            self.driver.close()
            print("✅ Neo4j connection closed")
    
    def get_driver(self):
        return self.driver
    
    def test_connection(self):
        """Test connection with a simple query"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                return record['test'] == 1
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

# Singleton instance
_neo4j_connection = None

def get_neo4j_connection():
    """Get or create Neo4j connection singleton"""
    global _neo4j_connection
    
    if _neo4j_connection is None:
        _neo4j_connection = Neo4jConnection()
    
    return _neo4j_connection.get_driver()

def close_neo4j_connection():
    """Close Neo4j connection"""
    global _neo4j_connection
    
    if _neo4j_connection:
        _neo4j_connection.close()
        _neo4j_connection = None
