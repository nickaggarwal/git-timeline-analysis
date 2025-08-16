from neo4j import GraphDatabase
from neo4j.time import DateTime as Neo4jDateTime
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from datetime import datetime
from src.models.schema import (
    Codebase, CommitHistory, Developer, Branch, BusinessMilestone,
    Neo4jNode, Neo4jRelationship, NodeType
)

logger = logging.getLogger(__name__)


def serialize_neo4j_value(obj):
    """Convert Neo4j-specific types to JSON-serializable formats"""
    if isinstance(obj, Neo4jDateTime):
        return obj.to_native().isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_neo4j_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_neo4j_value(item) for item in obj]
    else:
        return obj


class Neo4jService:
    def __init__(self, uri: str = "bolt://localhost:7687", username: str = "neo4j", password: str = "password"):
        try:
            # Simple initialization with minimal configuration
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {str(e)}")
            raise ConnectionError(f"Cannot connect to Neo4j: {str(e)}")
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
    
    def test_connection(self) -> bool:
        """Test the Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}")
            return False
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")
    
    def create_constraints(self):
        """Create unique constraints for better performance"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Codebase) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (cm:Commit) REQUIRE cm.sha IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Developer) REQUIRE d.email IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Branch) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:BusinessMilestone) REQUIRE m.id IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint creation failed (might already exist): {str(e)}")
    
    def create_codebase_node(self, codebase: Codebase) -> bool:
        """Create a codebase node in Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (c:Codebase {id: $id})
                    SET c.git_url = $git_url,
                        c.name = $name,
                        c.description = $description,
                        c.created_at = datetime($created_at),
                        c.last_analyzed = datetime($last_analyzed),
                        c.total_commits = $total_commits,
                        c.total_developers = $total_developers,
                        c.primary_language = $primary_language
                """, 
                    id=codebase.id,
                    git_url=str(codebase.git_url),
                    name=codebase.name,
                    description=codebase.description,
                    created_at=codebase.created_at.isoformat(),
                    last_analyzed=codebase.last_analyzed.isoformat() if codebase.last_analyzed else None,
                    total_commits=codebase.total_commits,
                    total_developers=codebase.total_developers,
                    primary_language=codebase.primary_language
                )
                return True
        except Exception as e:
            logger.error(f"Failed to create codebase node: {str(e)}")
            return False
    
    def create_developer_nodes(self, developers: List[Developer]) -> int:
        """Create developer nodes in Neo4j"""
        created_count = 0
        
        with self.driver.session() as session:
            for developer in developers:
                try:
                    session.run("""
                        MERGE (d:Developer {email: $email})
                        SET d.id = $id,
                            d.name = $name,
                            d.total_commits = $total_commits,
                            d.expertise_areas = $expertise_areas,
                            d.contribution_score = $contribution_score,
                            d.first_commit_date = datetime($first_commit_date),
                            d.last_commit_date = datetime($last_commit_date),
                            d.lines_added = $lines_added,
                            d.lines_removed = $lines_removed
                    """,
                        id=developer.id,
                        email=developer.email,
                        name=developer.name,
                        total_commits=developer.total_commits,
                        expertise_areas=developer.expertise_areas,
                        contribution_score=developer.contribution_score,
                        first_commit_date=developer.first_commit_date.isoformat() if developer.first_commit_date else None,
                        last_commit_date=developer.last_commit_date.isoformat() if developer.last_commit_date else None,
                        lines_added=developer.lines_added,
                        lines_removed=developer.lines_removed
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create developer node for {developer.email}: {str(e)}")
        
        logger.info(f"Created {created_count} developer nodes")
        return created_count
    
    def create_branch_nodes(self, branches: List[Branch], codebase_id: str) -> int:
        """Create branch nodes and link them to codebase"""
        created_count = 0
        
        with self.driver.session() as session:
            for branch in branches:
                try:
                    # Create branch node
                    session.run("""
                        MERGE (b:Branch {id: $id})
                        SET b.name = $name,
                            b.codebase_id = $codebase_id,
                            b.created_at = datetime($created_at),
                            b.last_commit_sha = $last_commit_sha,
                            b.is_main_branch = $is_main_branch,
                            b.total_commits = $total_commits
                    """,
                        id=branch.id,
                        name=branch.name,
                        codebase_id=branch.codebase_id,
                        created_at=branch.created_at.isoformat(),
                        last_commit_sha=branch.last_commit_sha,
                        is_main_branch=branch.is_main_branch,
                        total_commits=branch.total_commits
                    )
                    
                    # Link branch to codebase
                    session.run("""
                        MATCH (c:Codebase {id: $codebase_id})
                        MATCH (b:Branch {id: $branch_id})
                        MERGE (c)-[:HAS_BRANCH]->(b)
                    """,
                        codebase_id=codebase_id,
                        branch_id=branch.id
                    )
                    
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create branch node for {branch.name}: {str(e)}")
        
        logger.info(f"Created {created_count} branch nodes")
        return created_count
    
    def create_commit_nodes(self, commits: List[CommitHistory], codebase_id: str) -> int:
        """Create commit nodes and relationships"""
        created_count = 0
        
        with self.driver.session() as session:
            for commit in commits:
                try:
                    # Create commit node
                    session.run("""
                        MERGE (c:Commit {sha: $sha})
                        SET c.id = $id,
                            c.message = $message,
                            c.author_name = $author_name,
                            c.author_email = $author_email,
                            c.committer_name = $committer_name,
                            c.committer_email = $committer_email,
                            c.timestamp = datetime($timestamp),
                            c.branch = $branch,
                            c.files_changed = $files_changed,
                            c.insertions = $insertions,
                            c.deletions = $deletions,
                            c.parent_shas = $parent_shas,
                            c.feature_summary = $feature_summary,
                            c.business_impact = $business_impact,
                            c.complexity_score = $complexity_score
                    """,
                        id=commit.id,
                        sha=commit.sha,
                        message=commit.message,
                        author_name=commit.author_name,
                        author_email=commit.author_email,
                        committer_name=commit.committer_name,
                        committer_email=commit.committer_email,
                        timestamp=commit.timestamp.isoformat(),
                        branch=commit.branch,
                        files_changed=commit.files_changed,
                        insertions=commit.insertions,
                        deletions=commit.deletions,
                        parent_shas=commit.parent_shas,
                        feature_summary=commit.feature_summary,
                        business_impact=commit.business_impact,
                        complexity_score=commit.complexity_score
                    )
                    
                    # Link commit to codebase
                    session.run("""
                        MATCH (cb:Codebase {id: $codebase_id})
                        MATCH (c:Commit {sha: $commit_sha})
                        MERGE (cb)-[:CONTAINS_COMMIT]->(c)
                    """,
                        codebase_id=codebase_id,
                        commit_sha=commit.sha
                    )
                    
                    # Link commit to author
                    session.run("""
                        MATCH (d:Developer {email: $author_email})
                        MATCH (c:Commit {sha: $commit_sha})
                        MERGE (d)-[:AUTHORED {timestamp: datetime($timestamp)}]->(c)
                    """,
                        author_email=commit.author_email,
                        commit_sha=commit.sha,
                        timestamp=commit.timestamp.isoformat()
                    )
                    
                    # Create parent-child relationships
                    for parent_sha in commit.parent_shas:
                        session.run("""
                            MATCH (parent:Commit {sha: $parent_sha})
                            MATCH (child:Commit {sha: $child_sha})
                            MERGE (parent)-[:PARENT_OF]->(child)
                        """,
                            parent_sha=parent_sha,
                            child_sha=commit.sha
                        )
                    
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create commit node for {commit.sha}: {str(e)}")
        
        logger.info(f"Created {created_count} commit nodes")
        return created_count
    
    def create_milestone_nodes(self, milestones: List[BusinessMilestone]) -> int:
        """Create business milestone nodes and link to commits"""
        created_count = 0
        
        with self.driver.session() as session:
            for milestone in milestones:
                try:
                    # Create milestone node
                    session.run("""
                        MERGE (m:BusinessMilestone {id: $id})
                        SET m.name = $name,
                            m.description = $description,
                            m.date = datetime($date),
                            m.codebase_id = $codebase_id,
                            m.related_commits = $related_commits,
                            m.milestone_type = $milestone_type,
                            m.version = $version
                    """,
                        id=milestone.id,
                        name=milestone.name,
                        description=milestone.description,
                        date=milestone.date.isoformat(),
                        codebase_id=milestone.codebase_id,
                        related_commits=milestone.related_commits,
                        milestone_type=milestone.milestone_type,
                        version=milestone.version
                    )
                    
                    # Link milestone to codebase
                    session.run("""
                        MATCH (c:Codebase {id: $codebase_id})
                        MATCH (m:BusinessMilestone {id: $milestone_id})
                        MERGE (c)-[:HAS_MILESTONE]->(m)
                    """,
                        codebase_id=milestone.codebase_id,
                        milestone_id=milestone.id
                    )
                    
                    # Link milestone to related commits
                    for commit_sha in milestone.related_commits:
                        session.run("""
                            MATCH (m:BusinessMilestone {id: $milestone_id})
                            MATCH (c:Commit {sha: $commit_sha})
                            MERGE (m)-[:RELATES_TO]->(c)
                        """,
                            milestone_id=milestone.id,
                            commit_sha=commit_sha
                        )
                    
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create milestone node for {milestone.id}: {str(e)}")
        
        logger.info(f"Created {created_count} milestone nodes")
        return created_count
    
    def create_file_nodes_and_relationships(self, commits: List[CommitHistory]) -> int:
        """Create file nodes and their relationships with commits"""
        file_commits = {}
        
        # Collect all files and their commit relationships
        for commit in commits:
            for file_path in commit.files_changed:
                if file_path not in file_commits:
                    file_commits[file_path] = []
                file_commits[file_path].append(commit.sha)
        
        created_count = 0
        with self.driver.session() as session:
            for file_path, commit_shas in file_commits.items():
                try:
                    # Create file node
                    session.run("""
                        MERGE (f:File {path: $path})
                        SET f.name = $name,
                            f.extension = $extension,
                            f.directory = $directory,
                            f.total_commits = $total_commits
                    """,
                        path=file_path,
                        name=file_path.split('/')[-1],
                        extension=file_path.split('.')[-1] if '.' in file_path else '',
                        directory='/'.join(file_path.split('/')[:-1]),
                        total_commits=len(commit_shas)
                    )
                    
                    # Link file to commits that modified it
                    for commit_sha in commit_shas:
                        session.run("""
                            MATCH (f:File {path: $file_path})
                            MATCH (c:Commit {sha: $commit_sha})
                            MERGE (c)-[:MODIFIES]->(f)
                        """,
                            file_path=file_path,
                            commit_sha=commit_sha
                        )
                    
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create file node for {file_path}: {str(e)}")
        
        logger.info(f"Created {created_count} file nodes")
        return created_count
    
    def get_commit_graph_data(self, codebase_id: str) -> Dict[str, Any]:
        """Get graph data for visualization"""
        with self.driver.session() as session:
            # Get nodes
            nodes_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                OPTIONAL MATCH (commit)<-[:AUTHORED]-(dev:Developer)
                RETURN commit, dev
                LIMIT 1000
            """, codebase_id=codebase_id)
            
            nodes = []
            node_ids = set()
            
            for record in nodes_result:
                commit = record["commit"]
                developer = record["dev"]
                
                if commit["sha"] not in node_ids:
                    nodes.append({
                        "id": commit["sha"],
                        "type": "commit",
                        "properties": serialize_neo4j_value(dict(commit))
                    })
                    node_ids.add(commit["sha"])
                
                if developer and developer["email"] not in node_ids:
                    nodes.append({
                        "id": developer["email"],
                        "type": "developer",
                        "properties": serialize_neo4j_value(dict(developer))
                    })
                    node_ids.add(developer["email"])
            
            # Get relationships
            relationships_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                MATCH (commit)<-[r:AUTHORED]-(dev:Developer)
                RETURN dev.email as dev_email, commit.sha as commit_sha, type(r) as rel_type
                UNION
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                MATCH (commit)-[r:PARENT_OF]->(child:Commit)
                RETURN commit.sha as dev_email, child.sha as commit_sha, type(r) as rel_type
                LIMIT 5000
            """, codebase_id=codebase_id)
            
            relationships = []
            for record in relationships_result:
                relationships.append({
                    "source": record["dev_email"],
                    "target": record["commit_sha"],
                    "type": record["rel_type"]
                })
            
            return {
                "nodes": nodes,
                "relationships": relationships,
                "stats": {
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships)
                }
            }
    
    def get_developer_expertise_data(self, codebase_id: str) -> List[Dict[str, Any]]:
        """Get developer expertise data from the graph"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                MATCH (commit)<-[:AUTHORED]-(dev:Developer)
                RETURN dev.name as name, 
                       dev.email as email,
                       dev.expertise_areas as expertise_areas,
                       dev.contribution_score as contribution_score,
                       dev.total_commits as total_commits,
                       dev.lines_added as lines_added,
                       dev.lines_removed as lines_removed
                ORDER BY dev.contribution_score DESC
            """, codebase_id=codebase_id)
            
            return [serialize_neo4j_value(dict(record)) for record in result]