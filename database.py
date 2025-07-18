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
    
    def setup_movie_data(self):
        """Populate the database with movie data"""
        movies_query = """
        LOAD CSV WITH HEADERS FROM 
        'https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv'
        AS row
        MERGE (m:Movie {id:row.movieId})
        SET m.released = date(row.released),
            m.title = row.title,
            m.imdbRating = toFloat(row.imdbRating)
        FOREACH (director in split(row.director, '|') | 
            MERGE (p:Person {name:trim(director)})
            MERGE (p)-[:DIRECTED]->(m))
        FOREACH (actor in split(row.actors, '|') | 
            MERGE (p:Person {name:trim(actor)})
            MERGE (p)-[:ACTED_IN]->(m))
        FOREACH (genre in split(row.genres, '|') | 
            MERGE (g:Genre {name:trim(genre)})
            MERGE (m)-[:IN_GENRE]->(g))
        """
        
        try:
            self.graph.query(movies_query)
            print("✅ Movie data successfully loaded into Neo4j")
        except Exception as e:
            print(f"❌ Error loading movie data: {e}")
    
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