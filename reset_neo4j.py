#!/usr/bin/env python3
"""
Neo4j Database Reset Script
This script clears all data from the Neo4j database and recreates the constraints.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.services.neo4j_service import Neo4jService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_neo4j_database():
    """Reset the Neo4j database by clearing all data and recreating constraints"""
    
    # Initialize Neo4j service with default credentials
    neo4j_service = Neo4jService()
    
    try:
        # Test connection first
        if not neo4j_service.test_connection():
            logger.error("Failed to connect to Neo4j database. Please ensure Neo4j is running.")
            return False
        
        logger.info("Connected to Neo4j successfully")
        
        # Clear all data
        logger.info("Clearing all data from Neo4j database...")
        neo4j_service.clear_database()
        
        # Recreate constraints
        logger.info("Recreating database constraints...")
        neo4j_service.create_constraints()
        
        logger.info("Neo4j database has been reset successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset Neo4j database: {str(e)}")
        return False
        
    finally:
        # Close the connection
        neo4j_service.close()

if __name__ == "__main__":
    print("🔄 Resetting Neo4j Database...")
    print("=" * 50)
    
    success = reset_neo4j_database()
    
    if success:
        print("✅ Neo4j database reset completed successfully!")
    else:
        print("❌ Neo4j database reset failed!")
        sys.exit(1)