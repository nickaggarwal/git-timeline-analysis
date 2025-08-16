import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import tempfile
import shutil
from dotenv import load_dotenv

from src.services.git_service import GitService
from src.services.analysis_service import AnalysisService
from src.services.neo4j_service import Neo4jService
from src.models.schema import AnalysisRequest, Codebase

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CodebaseAnalyzer:
    """Main orchestration service for analyzing codebases and building knowledge graphs"""
    
    def __init__(self, 
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_username: str = "neo4j", 
                 neo4j_password: str = "password",
                 openai_api_key: Optional[str] = None):
        
        # Load configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', neo4j_uri)
        neo4j_username = os.getenv('NEO4J_USERNAME', neo4j_username)
        neo4j_password = os.getenv('NEO4J_PASSWORD', neo4j_password)
        
        # Initialize services
        self.git_service = GitService()
        self.analysis_service = AnalysisService(openai_api_key)
        self.neo4j_service = Neo4jService(neo4j_uri, neo4j_username, neo4j_password)
        
        # Log Azure OpenAI configuration status
        use_azure = os.getenv('USE_AZURE_OPENAI', 'false').lower() == 'true'
        if use_azure:
            logger.info("Azure OpenAI integration enabled")
        elif openai_api_key:
            logger.info("OpenAI integration enabled")
        else:
            logger.info("LLM analysis disabled - using basic analysis only")
        
        # Test Neo4j connection
        if not self.neo4j_service.test_connection():
            raise ConnectionError("Failed to connect to Neo4j database")
        
        # Create constraints for better performance
        self.neo4j_service.create_constraints()
    
    def analyze_repository(self, request: AnalysisRequest) -> Dict[str, Any]:
        """
        Complete analysis pipeline:
        1. Clone repository
        2. Extract git data (commits, developers, branches)
        3. Run LLM analysis on commits
        4. Build Neo4j graph with all relationships
        5. Return analysis summary
        """
        
        analysis_start = datetime.now()
        git_url = str(request.git_url)
        
        logger.info(f"Starting analysis of repository: {git_url}")
        
        try:
            # Step 1: Clone repository
            logger.info("Step 1: Cloning repository...")
            repo_path = self.git_service.clone_repository(git_url)
            
            # Step 2: Extract basic codebase info
            logger.info("Step 2: Extracting codebase information...")
            codebase = self.git_service.get_codebase_info(git_url)
            codebase.last_analyzed = analysis_start
            
            # Step 3: Extract branches
            logger.info("Step 3: Extracting branch information...")
            branches = self.git_service.get_all_branches()
            
            # Step 4: Extract developers
            logger.info("Step 4: Extracting developer information...")
            developers = self.git_service.get_developers()
            
            # Step 5: Extract commit history (limited by user preference)
            logger.info("Step 5: Extracting commit history...")
            max_commits = request.max_commits or 100  # Use user preference or default to 100
            commits = self.git_service.get_commit_history(max_count=max_commits)
            logger.info(f"Retrieved {len(commits)} commits (limit: {max_commits})")
            
            # Step 6: Run LLM analysis on commits (if enabled)
            if request.include_llm_analysis and commits:
                logger.info("Step 6: Running LLM analysis on commits...")
                # Analyze a subset of commits for LLM processing (to save API costs)
                llm_commit_limit = min(50, max_commits // 2)  # Analyze up to 50 or half of total commits
                top_commits = commits[:llm_commit_limit] if len(commits) > llm_commit_limit else commits
                logger.info(f"Running LLM analysis on {len(top_commits)} commits")
                
                for i, commit in enumerate(top_commits):
                    try:
                        logger.info(f"Analyzing commit {i+1}/{len(top_commits)}: {commit.sha[:8]}")
                        commit.feature_summary = self.analysis_service.generate_feature_summary(commit)
                        commit.business_impact = self.analysis_service.analyze_business_impact(commit)
                    except Exception as e:
                        logger.warning(f"Failed to analyze commit {commit.sha}: {str(e)}")
                        continue
            
            # Step 7: Identify business milestones
            logger.info("Step 7: Identifying business milestones...")
            milestones = self.analysis_service.identify_business_milestones(commits, codebase.id)
            
            # Step 8: Build Neo4j graph
            logger.info("Step 8: Building Neo4j graph...")
            graph_stats = self._build_neo4j_graph(codebase, developers, branches, commits, milestones)
            
            # Step 9: Generate analysis summary
            analysis_end = datetime.now()
            analysis_duration = (analysis_end - analysis_start).total_seconds()
            
            summary = {
                "codebase_id": codebase.id,
                "analysis_timestamp": analysis_start.isoformat(),
                "analysis_duration_seconds": analysis_duration,
                "repository_url": git_url,
                "stats": {
                    "total_commits": len(commits),
                    "total_developers": len(developers),
                    "total_branches": len(branches),
                    "total_milestones": len(milestones),
                    "primary_language": codebase.primary_language,
                    "commits_with_llm_analysis": sum(1 for c in commits if c.feature_summary),
                    "date_range": {
                        "earliest_commit": min(c.timestamp for c in commits).isoformat() if commits else None,
                        "latest_commit": max(c.timestamp for c in commits).isoformat() if commits else None
                    }
                },
                "neo4j_stats": graph_stats,
                "top_contributors": [
                    {
                        "name": dev.name,
                        "email": dev.email,
                        "commits": dev.total_commits,
                        "contribution_score": dev.contribution_score,
                        "expertise_areas": dev.expertise_areas
                    } for dev in sorted(developers, key=lambda x: x.contribution_score, reverse=True)[:10]
                ],
                "recent_milestones": [
                    {
                        "name": milestone.name,
                        "type": milestone.milestone_type,
                        "date": milestone.date.isoformat(),
                        "version": milestone.version
                    } for milestone in sorted(milestones, key=lambda x: x.date, reverse=True)[:5]
                ]
            }
            
            logger.info(f"Analysis completed successfully in {analysis_duration:.2f} seconds")
            return summary
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
        finally:
            # Cleanup
            self.git_service.cleanup()
    
    def _build_neo4j_graph(self, codebase: Codebase, developers: List, branches: List, 
                          commits: List, milestones: List) -> Dict[str, int]:
        """Build the complete Neo4j graph with all entities and relationships"""
        
        stats = {
            "codebase_nodes": 0,
            "developer_nodes": 0,
            "branch_nodes": 0,
            "commit_nodes": 0,
            "milestone_nodes": 0,
            "file_nodes": 0
        }
        
        try:
            # Create codebase node
            if self.neo4j_service.create_codebase_node(codebase):
                stats["codebase_nodes"] = 1
            
            # Create developer nodes
            stats["developer_nodes"] = self.neo4j_service.create_developer_nodes(developers)
            
            # Create branch nodes
            stats["branch_nodes"] = self.neo4j_service.create_branch_nodes(branches, codebase.id)
            
            # Create commit nodes (this also creates relationships to developers and codebase)
            stats["commit_nodes"] = self.neo4j_service.create_commit_nodes(commits, codebase.id)
            
            # Create milestone nodes
            stats["milestone_nodes"] = self.neo4j_service.create_milestone_nodes(milestones)
            
            # Create file nodes and relationships
            stats["file_nodes"] = self.neo4j_service.create_file_nodes_and_relationships(commits)
            
            logger.info(f"Neo4j graph built successfully: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to build Neo4j graph: {str(e)}")
            raise
    
    def get_codebase_summary(self, codebase_id: str) -> Dict[str, Any]:
        """Get a summary of an analyzed codebase from Neo4j"""
        try:
            # Get graph visualization data
            graph_data = self.neo4j_service.get_commit_graph_data(codebase_id)
            
            # Get developer expertise data
            developer_data = self.neo4j_service.get_developer_expertise_data(codebase_id)
            
            return {
                "codebase_id": codebase_id,
                "graph_data": graph_data,
                "developer_expertise": developer_data,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get codebase summary for {codebase_id}: {str(e)}")
            raise
    
    def search_commits_by_pattern(self, codebase_id: str, pattern: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search commits by message pattern using Neo4j"""
        with self.neo4j_service.driver.session() as session:
            result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                WHERE commit.message =~ $pattern
                RETURN commit.sha as sha,
                       commit.message as message,
                       commit.author_name as author,
                       commit.timestamp as timestamp,
                       commit.feature_summary as feature_summary,
                       commit.business_impact as business_impact
                ORDER BY commit.timestamp DESC
                LIMIT $limit
            """, 
                codebase_id=codebase_id,
                pattern=f"(?i).*{pattern}.*",  # Case-insensitive regex
                limit=limit
            )
            
            return [dict(record) for record in result]
    
    def get_developer_collaboration_patterns(self, codebase_id: str) -> Dict[str, Any]:
        """Analyze collaboration patterns between developers"""
        with self.neo4j_service.driver.session() as session:
            # Find files touched by multiple developers
            result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                MATCH (commit)-[:MODIFIES]->(file:File)
                MATCH (commit)<-[:AUTHORED]-(dev:Developer)
                WITH file.path as file_path, collect(DISTINCT dev.name) as developers
                WHERE size(developers) > 1
                RETURN file_path, developers, size(developers) as dev_count
                ORDER BY dev_count DESC
                LIMIT 20
            """, codebase_id=codebase_id)
            
            collaboration_files = [dict(record) for record in result]
            
            # Find developer pairs who often work on same files
            pairs_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit1:Commit)
                MATCH (c)-[:CONTAINS_COMMIT]->(commit2:Commit)
                MATCH (commit1)-[:MODIFIES]->(file:File)<-[:MODIFIES]-(commit2)
                MATCH (commit1)<-[:AUTHORED]-(dev1:Developer)
                MATCH (commit2)<-[:AUTHORED]-(dev2:Developer)
                WHERE dev1.email < dev2.email  // Avoid duplicates
                WITH dev1.name as dev1_name, dev2.name as dev2_name, count(DISTINCT file) as shared_files
                WHERE shared_files > 2
                RETURN dev1_name, dev2_name, shared_files
                ORDER BY shared_files DESC
                LIMIT 15
            """, codebase_id=codebase_id)
            
            collaboration_pairs = [dict(record) for record in pairs_result]
            
            return {
                "collaboration_files": collaboration_files,
                "collaboration_pairs": collaboration_pairs
            }
    
    def close(self):
        """Close all service connections"""
        self.neo4j_service.close()
        self.git_service.cleanup()