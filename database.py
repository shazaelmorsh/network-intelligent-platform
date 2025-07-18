from langchain_neo4j import Neo4jGraph
from config import Config

class DatabaseManager:
    """Manages Neo4j database connection and operations"""
    
    def __init__(self):
        self.graph = Neo4jGraph(
            url=Config.NEO4J_URI,
            username=Config.NEO4J_USERNAME,
            password=Config.NEO4J_PASSWORD,
            enhanced_schema=True
        )
    
    
    def refresh_schema(self):
        """Refresh the database schema"""
        self.graph.refresh_schema()
        return self.graph.schema
    
    def get_schema(self):
        """Get the current database schema"""
        return self.graph.schema
    
    def get_enhanced_schema(self):
        """Get the enhanced schema with detailed property information"""
        return self.graph.schema
    
    def query(self, cypher_query, parameters=None):
        """Execute a Cypher query"""
        return self.graph.query(cypher_query, parameters)
    
    def test_connection(self):
        """Test the database connection"""
        try:
            result = self.query("RETURN 1 as test")
            print("✅ Successfully connected to Neo4j")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            return False 