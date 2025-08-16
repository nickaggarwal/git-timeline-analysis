#!/usr/bin/env python3
"""
Test Neo4j connection and run sample queries
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add the backend src directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv('../.env')

from src.services.neo4j_service import Neo4jService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """Test Neo4j connection and run sample queries"""
    
    try:
        # Get Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        
        logger.info(f"🔌 Connecting to Neo4j at {neo4j_uri}")
        
        # Initialize Neo4j service
        neo4j_service = Neo4jService(neo4j_uri, neo4j_username, neo4j_password)
        
        # Test 1: Basic connection test
        logger.info("🧪 Test 1: Basic connection test...")
        connection_ok = neo4j_service.test_connection()
        if connection_ok:
            logger.info("✅ Connection successful!")
        else:
            logger.error("❌ Connection failed!")
            return False
        
        # Test 2: Clear database (if exists)
        logger.info("🧪 Test 2: Clearing existing data...")
        neo4j_service.clear_database()
        logger.info("✅ Database cleared")
        
        # Test 3: Create constraints
        logger.info("🧪 Test 3: Creating constraints...")
        neo4j_service.create_constraints()
        logger.info("✅ Constraints created")
        
        # Test 4: Create sample nodes
        logger.info("🧪 Test 4: Creating sample nodes...")
        with neo4j_service.driver.session() as session:
            # Create a test codebase
            session.run("""
                CREATE (c:Codebase {
                    id: 'test-repo',
                    name: 'Test Repository', 
                    git_url: 'https://github.com/test/repo',
                    created_at: datetime(),
                    total_commits: 5,
                    total_developers: 2,
                    primary_language: 'Python'
                })
            """)
            
            # Create test developers
            session.run("""
                CREATE (d1:Developer {
                    id: 'dev1',
                    name: 'Alice Developer',
                    email: 'alice@example.com',
                    total_commits: 3,
                    contribution_score: 85.5
                }),
                (d2:Developer {
                    id: 'dev2', 
                    name: 'Bob Coder',
                    email: 'bob@example.com',
                    total_commits: 2,
                    contribution_score: 70.0
                })
            """)
            
            # Create test commits
            session.run("""
                CREATE (c1:Commit {
                    sha: 'abc123',
                    message: 'Initial commit',
                    author_name: 'Alice Developer',
                    author_email: 'alice@example.com',
                    timestamp: datetime(),
                    insertions: 100,
                    deletions: 0
                }),
                (c2:Commit {
                    sha: 'def456',
                    message: 'Add new feature',
                    author_name: 'Bob Coder', 
                    author_email: 'bob@example.com',
                    timestamp: datetime(),
                    insertions: 50,
                    deletions: 10
                })
            """)
            
            # Create relationships
            session.run("""
                MATCH (c:Codebase {id: 'test-repo'})
                MATCH (commit:Commit)
                MERGE (c)-[:CONTAINS_COMMIT]->(commit)
            """)
            
            session.run("""
                MATCH (d:Developer), (c:Commit)
                WHERE d.email = c.author_email
                MERGE (d)-[:AUTHORED]->(c)
            """)
            
        logger.info("✅ Sample data created")
        
        # Test 5: Query the data
        logger.info("🧪 Test 5: Querying sample data...")
        with neo4j_service.driver.session() as session:
            # Query 1: Get all nodes
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
            logger.info("📊 Node counts:")
            for record in result:
                logger.info(f"   - {record['labels']}: {record['count']}")
            
            # Query 2: Get codebase summary
            result = session.run("""
                MATCH (c:Codebase)-[:CONTAINS_COMMIT]->(commit:Commit)<-[:AUTHORED]-(dev:Developer)
                RETURN c.name as codebase, 
                       count(DISTINCT commit) as total_commits,
                       count(DISTINCT dev) as total_developers,
                       collect(DISTINCT dev.name) as developer_names
            """)
            for record in result:
                logger.info(f"📈 Codebase: {record['codebase']}")
                logger.info(f"   - Commits: {record['total_commits']}")
                logger.info(f"   - Developers: {record['total_developers']}")
                logger.info(f"   - Developer names: {record['developer_names']}")
            
            # Query 3: Test graph data retrieval
            graph_data = neo4j_service.get_commit_graph_data('test-repo')
            logger.info(f"🕸️ Graph data: {graph_data['stats']['total_nodes']} nodes, {graph_data['stats']['total_relationships']} relationships")
        
        # Test 6: Clean up
        logger.info("🧪 Test 6: Cleaning up...")
        neo4j_service.clear_database()
        logger.info("✅ Cleanup complete")
        
        logger.info("🎉 All Neo4j tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Neo4j test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            neo4j_service.close()
        except:
            pass

if __name__ == "__main__":
    print("🕰️ Codebase Time Machine - Neo4j Connection Test")
    print("=" * 60)
    success = test_neo4j_connection()
    sys.exit(0 if success else 1)