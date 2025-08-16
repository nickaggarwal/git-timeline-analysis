#!/usr/bin/env python3
"""
Check what data is currently in Neo4j
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

def check_neo4j_data():
    """Check current Neo4j database contents"""
    
    try:
        # Get Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        neo4j_username = os.getenv('NEO4J_USERNAME', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        
        logger.info(f"🔌 Connecting to Neo4j at {neo4j_uri}")
        
        # Initialize Neo4j service
        neo4j_service = Neo4jService(neo4j_uri, neo4j_username, neo4j_password)
        
        # Test connection
        if not neo4j_service.test_connection():
            logger.error("❌ Cannot connect to Neo4j")
            return False
        
        logger.info("✅ Connected to Neo4j successfully")
        
        with neo4j_service.driver.session() as session:
            # Check total node and relationship counts
            logger.info("📊 Database Overview:")
            
            # Use basic query without APOC
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record["label"] for record in result]
            
            labels_counts = []
            for label in labels:
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = count_result.single()["count"]
                labels_counts.append({"label": label, "count": count})
            
            labels_counts.sort(key=lambda x: x["count"], reverse=True)
            
            total_nodes = sum(item["count"] for item in labels_counts)
            
            if total_nodes == 0:
                logger.info("🗃️ Database is empty - no nodes found")
            else:
                logger.info(f"📈 Total nodes: {total_nodes}")
                for item in labels_counts:
                    logger.info(f"   - {item['label']}: {item['count']} nodes")
            
            # Count relationships
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = rel_result.single()["rel_count"]
            logger.info(f"🔗 Total relationships: {rel_count}")
            
            # If we have data, show some examples
            if total_nodes > 0:
                logger.info("\n📋 Sample Data:")
                
                # Show some codebases if any
                codebase_result = session.run("""
                    MATCH (c:Codebase)
                    RETURN c.id as id, c.name as name, c.git_url as git_url
                    LIMIT 5
                """)
                codebases = [dict(record) for record in codebase_result]
                if codebases:
                    logger.info("🏗️ Codebases:")
                    for cb in codebases:
                        logger.info(f"   - {cb['name']} ({cb['id']}): {cb['git_url']}")
                
                # Show some commits if any
                commit_result = session.run("""
                    MATCH (c:Commit)
                    RETURN c.sha as sha, c.message as message, c.author_name as author
                    LIMIT 5
                """)
                commits = [dict(record) for record in commit_result]
                if commits:
                    logger.info("📝 Recent Commits:")
                    for commit in commits:
                        message = commit['message'][:60] + "..." if len(commit['message']) > 60 else commit['message']
                        logger.info(f"   - {commit['sha'][:8]}: {message} (by {commit['author']})")
                
                # Show some developers if any
                dev_result = session.run("""
                    MATCH (d:Developer)
                    RETURN d.name as name, d.email as email, d.total_commits as commits
                    ORDER BY d.total_commits DESC
                    LIMIT 5
                """)
                developers = [dict(record) for record in dev_result]
                if developers:
                    logger.info("👥 Top Developers:")
                    for dev in developers:
                        logger.info(f"   - {dev['name']} ({dev['email']}): {dev['commits']} commits")
            
        logger.info("🎉 Neo4j data check completed!")
        return total_nodes > 0
        
    except Exception as e:
        logger.error(f"❌ Neo4j data check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            neo4j_service.close()
        except:
            pass

if __name__ == "__main__":
    print("🕰️ Codebase Time Machine - Neo4j Data Check")
    print("=" * 60)
    has_data = check_neo4j_data()
    
    if has_data:
        print("\n✅ Neo4j contains data!")
    else:
        print("\n📭 Neo4j is empty or has no data")
    
    sys.exit(0)