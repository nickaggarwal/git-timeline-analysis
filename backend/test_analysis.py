#!/usr/bin/env python3
"""
Test script to verify the Codebase Time Machine analysis pipeline
This script will analyze a small public repository and dump data into Neo4j
"""

import sys
import os
import logging
from datetime import datetime

# Add the backend directory to Python path for proper imports
sys.path.insert(0, os.path.dirname(__file__))

from src.models.schema import AnalysisRequest
from src.services.codebase_analyzer import CodebaseAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_analysis():
    """Test the complete analysis pipeline"""
    
    print("🚀 Starting Codebase Time Machine Test")
    print("=" * 50)
    
    # Configuration
    test_repo_url = "https://github.com/octocat/Hello-World.git"  # Small test repo
    
    # Neo4j connection settings (adjust as needed)
    neo4j_config = {
        "neo4j_uri": "neo4j://127.0.0.1:7687",
        "neo4j_username": "neo4j", 
        "neo4j_password": "password"  # Change this to your actual password
    }
    
    try:
        # Initialize the analyzer
        print("🔧 Initializing CodebaseAnalyzer...")
        analyzer = CodebaseAnalyzer(
            **neo4j_config,
            openai_api_key=None  # Set to None to skip LLM analysis for now
        )
        
        # Create analysis request
        request = AnalysisRequest(
            git_url=test_repo_url,
            include_llm_analysis=False  # Disable for initial test
        )
        
        print(f"📊 Analyzing repository: {test_repo_url}")
        print("This may take a few minutes...")
        
        # Run the analysis
        result = analyzer.analyze_repository(request)
        
        # Display results
        print("\n✅ Analysis completed successfully!")
        print("=" * 50)
        print(f"📈 Analysis Summary:")
        print(f"  • Repository: {result['repository_url']}")
        print(f"  • Codebase ID: {result['codebase_id']}")
        print(f"  • Analysis Duration: {result['analysis_duration_seconds']:.2f} seconds")
        print(f"  • Primary Language: {result['stats']['primary_language']}")
        print(f"  • Total Commits: {result['stats']['total_commits']}")
        print(f"  • Total Developers: {result['stats']['total_developers']}")
        print(f"  • Total Branches: {result['stats']['total_branches']}")
        print(f"  • Total Milestones: {result['stats']['total_milestones']}")
        
        print(f"\n🔗 Neo4j Graph Stats:")
        neo4j_stats = result['neo4j_stats']
        for key, value in neo4j_stats.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n👥 Top Contributors:")
        for i, contributor in enumerate(result['top_contributors'][:5], 1):
            print(f"  {i}. {contributor['name']} ({contributor['email']})")
            print(f"     Commits: {contributor['commits']}, Score: {contributor['contribution_score']}")
            print(f"     Expertise: {', '.join(contributor['expertise_areas'])}")
        
        if result['recent_milestones']:
            print(f"\n🎯 Recent Milestones:")
            for milestone in result['recent_milestones']:
                print(f"  • {milestone['name']} ({milestone['type']}) - {milestone['date'][:10]}")
        
        print(f"\n🎉 CHECKPOINT REACHED: Data successfully dumped into Neo4j!")
        print(f"✅ Graph database contains:")
        print(f"   - {neo4j_stats.get('commit_nodes', 0)} commit nodes")
        print(f"   - {neo4j_stats.get('developer_nodes', 0)} developer nodes") 
        print(f"   - {neo4j_stats.get('file_nodes', 0)} file nodes")
        print(f"   - Complete relationship graph with authorship and file changes")
        
        # Test graph retrieval
        print(f"\n🔍 Testing graph data retrieval...")
        codebase_summary = analyzer.get_codebase_summary(result['codebase_id'])
        graph_data = codebase_summary['graph_data']
        print(f"✅ Successfully retrieved graph with {graph_data['stats']['total_nodes']} nodes and {graph_data['stats']['total_relationships']} relationships")
        
        # Clean up
        analyzer.close()
        
        return True
        
    except ConnectionError as e:
        print(f"❌ Neo4j Connection Error: {e}")
        print("💡 Make sure Neo4j is running at bolt://localhost:7687")
        print("💡 Check your username/password configuration")
        return False
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    try:
        import git
        print("✅ GitPython is available")
    except ImportError:
        print("❌ GitPython not found. Install with: pip install gitpython")
        return False
    
    try:
        import neo4j
        print("✅ Neo4j driver is available") 
    except ImportError:
        print("❌ Neo4j driver not found. Install with: pip install neo4j")
        return False
    
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("neo4j://127.0.0.1:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        print("✅ Neo4j connection successful")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("💡 Make sure Neo4j is running and credentials are correct")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Codebase Time Machine - Analysis Pipeline Test")
    print("=" * 60)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("\n" + "="*60)
    success = test_analysis()
    
    if success:
        print("\n🎉 SUCCESS: Complete pipeline test passed!")
        print("🎯 CHECKPOINT: Data has been successfully analyzed and dumped into Neo4j")
        print("\nNext steps:")
        print("  1. Open Neo4j Browser (http://localhost:7474)")
        print("  2. Run: MATCH (n) RETURN n LIMIT 25")
        print("  3. Explore the commit graph and relationships")
    else:
        print("\n❌ FAILED: Pipeline test failed. Check the errors above.")
        sys.exit(1)