#!/usr/bin/env python3
"""
Test script to analyze triton-co-pilot repository directly
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv('../.env')

from src.services.git_service import GitService  
from src.services.analysis_service import AnalysisService
from src.models.schema import AnalysisRequest
from pydantic import HttpUrl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_triton_analysis():
    """Test the analysis pipeline on triton-co-pilot repository"""
    
    try:
        git_url = "https://github.com/inferless/triton-co-pilot"
        logger.info(f"🚀 Starting analysis of {git_url}")
        
        # Initialize services (skip Neo4j for now)
        git_service = GitService()
        analysis_service = AnalysisService()  # Will use Azure OpenAI from .env
        
        # Step 1: Clone repository
        logger.info("📥 Step 1: Cloning repository...")
        repo_path = git_service.clone_repository(git_url)
        logger.info(f"✅ Repository cloned to: {repo_path}")
        
        # Step 2: Get codebase info
        logger.info("🔍 Step 2: Extracting codebase information...")
        codebase = git_service.get_codebase_info(git_url)
        logger.info(f"✅ Codebase: {codebase.name} ({codebase.primary_language})")
        
        # Step 3: Get developers
        logger.info("👥 Step 3: Extracting developers...")
        developers = git_service.get_developers()
        logger.info(f"✅ Found {len(developers)} developers")
        for dev in developers[:5]:  # Show first 5
            logger.info(f"   - {dev.name} ({dev.email}): {dev.total_commits} commits")
        
        # Step 4: Get commit history (limited)
        logger.info("📝 Step 4: Extracting commit history...")
        commits = git_service.get_commit_history(max_count=10)  # Limit for demo
        logger.info(f"✅ Found {len(commits)} commits")
        
        # Step 5: Run Azure OpenAI analysis on commits
        logger.info("🤖 Step 5: Running Azure OpenAI analysis...")
        for i, commit in enumerate(commits[:5]):  # Analyze top 5 commits
            logger.info(f"   Analyzing commit {i+1}/5: {commit.sha[:8]} - {commit.message[:50]}...")
            try:
                commit.feature_summary = analysis_service.generate_feature_summary(commit)
                commit.business_impact = analysis_service.analyze_business_impact(commit)
                logger.info(f"   ✅ Feature: {commit.feature_summary}")
                logger.info(f"   📊 Impact: {commit.business_impact}")
            except Exception as e:
                logger.warning(f"   ⚠️ Analysis failed: {str(e)}")
        
        # Step 6: Analyze patterns
        logger.info("📈 Step 6: Analyzing commit patterns...")
        patterns = analysis_service.analyze_commit_patterns(commits)
        logger.info(f"✅ Pattern analysis complete:")
        logger.info(f"   - Total commits: {patterns.get('total_commits', 0)}")
        logger.info(f"   - Active developers: {len(patterns.get('developer_activity', {}))}")
        logger.info(f"   - Commit sizes: {patterns.get('commit_size_distribution', {})}")
        
        # Step 7: Identify milestones
        logger.info("🏁 Step 7: Identifying milestones...")
        milestones = analysis_service.identify_business_milestones(commits, codebase.id)
        logger.info(f"✅ Found {len(milestones)} potential milestones")
        for milestone in milestones[:3]:  # Show first 3
            logger.info(f"   - {milestone.name} ({milestone.milestone_type})")
        
        logger.info("🎉 Analysis completed successfully!")
        logger.info(f"📊 Final Summary:")
        logger.info(f"   - Repository: {git_url}")
        logger.info(f"   - Developers: {len(developers)}")
        logger.info(f"   - Commits analyzed: {len(commits)}")
        logger.info(f"   - LLM-enhanced commits: {sum(1 for c in commits if c.feature_summary)}")
        logger.info(f"   - Business milestones: {len(milestones)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}")
        return False
    finally:
        # Cleanup
        try:
            git_service.cleanup()
        except:
            pass

if __name__ == "__main__":
    print("🕰️ Codebase Time Machine - Triton Co-pilot Analysis")
    print("=" * 60)
    success = test_triton_analysis()
    sys.exit(0 if success else 1)