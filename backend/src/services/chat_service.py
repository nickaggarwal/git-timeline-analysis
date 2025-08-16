import logging
import re
from typing import List, Dict, Any, Set, Tuple
from src.services.neo4j_service import Neo4jService, serialize_neo4j_value
from src.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, neo4j_service: Neo4jService, analysis_service: AnalysisService):
        self.neo4j_service = neo4j_service
        self.analysis_service = analysis_service
        
        # Keywords for different node types
        self.node_keywords = {
            'commit': ['commit', 'change', 'fix', 'bug', 'feature', 'implementation', 'update', 'add', 'remove', 'refactor'],
            'developer': ['developer', 'author', 'contributor', 'engineer', 'programmer', 'who', 'person', 'team'],
            'file': ['file', 'code', 'source', 'script', 'module', 'class', 'function'],
            'milestone': ['milestone', 'release', 'version', 'launch', 'deployment', 'tag'],
            'branch': ['branch', 'main', 'master', 'develop', 'feature-branch']
        }
        
        # Relationship keywords
        self.relationship_keywords = {
            'AUTHORED': ['authored', 'written by', 'created by', 'developed by', 'who wrote', 'who made'],
            'CONTAINS_COMMIT': ['contains', 'includes', 'has commits'],
            'MODIFIES': ['modifies', 'changes', 'updates', 'affects', 'touches'],
            'PARENT_OF': ['parent', 'follows', 'after', 'before', 'sequence'],
            'HAS_MILESTONE': ['milestone', 'achieved', 'reached', 'released']
        }

    def extract_keywords_from_query(self, query: str) -> Dict[str, Set[str]]:
        """Extract relevant keywords and match them to node/relationship types"""
        query_lower = query.lower()
        keywords = re.findall(r'\b\w+\b', query_lower)
        
        extracted = {
            'node_types': set(),
            'relationships': set(),
            'search_terms': set()
        }
        
        # Match node type keywords
        for node_type, type_keywords in self.node_keywords.items():
            if any(keyword in keywords for keyword in type_keywords):
                extracted['node_types'].add(node_type)
        
        # Match relationship keywords
        for rel_type, rel_keywords in self.relationship_keywords.items():
            if any(keyword in query_lower for keyword in rel_keywords):
                extracted['relationships'].add(rel_type)
        
        # Extract potential search terms (names, technical terms, etc.)
        for word in keywords:
            if len(word) > 3 and word not in ['what', 'when', 'where', 'which', 'this', 'that', 'they', 'them']:
                extracted['search_terms'].add(word)
        
        return extracted

    def build_context_cypher_queries(self, codebase_id: str, keywords: Dict[str, Set[str]]) -> List[Tuple[str, str]]:
        """Build Cypher queries to gather relevant context"""
        queries = []
        
        # Base codebase check
        base_query = f"""
        MATCH (c:Codebase {{id: $codebase_id}})
        """
        
        # Query 1: Get relevant commits based on message content
        if keywords['search_terms']:
            search_pattern = '|'.join(keywords['search_terms'])
            commit_query = f"""
            {base_query}
            -[:CONTAINS_COMMIT]->(commit:Commit)
            OPTIONAL MATCH (commit)<-[:AUTHORED]-(dev:Developer)
            OPTIONAL MATCH (commit)-[:MODIFIES]->(file:File)
            WHERE commit.message =~ '(?i).*({search_pattern}).*'
               OR commit.feature_summary =~ '(?i).*({search_pattern}).*'
               OR commit.business_impact =~ '(?i).*({search_pattern}).*'
            RETURN 
                commit.sha as commit_sha,
                commit.message as commit_message,
                commit.feature_summary as feature_summary,
                commit.business_impact as business_impact,
                commit.timestamp as timestamp,
                commit.insertions as insertions,
                commit.deletions as deletions,
                dev.name as author_name,
                dev.email as author_email,
                collect(DISTINCT file.name) as files_modified
            ORDER BY commit.timestamp DESC
            LIMIT 5
            """
            queries.append(("relevant_commits", commit_query))
        
        # Query 2: Get developers and their expertise
        if 'developer' in keywords['node_types'] or keywords['search_terms']:
            dev_terms = keywords['search_terms'] if keywords['search_terms'] else ['']
            dev_pattern = '|'.join(dev_terms) if dev_terms != [''] else '.*'
            developer_query = f"""
            {base_query}
            -[:CONTAINS_COMMIT]->(commit:Commit)
            <-[:AUTHORED]-(dev:Developer)
            WHERE dev.name =~ '(?i).*({dev_pattern}).*' 
               OR dev.email =~ '(?i).*({dev_pattern}).*'
               OR any(area in dev.expertise_areas WHERE area =~ '(?i).*({dev_pattern}).*')
            RETURN 
                dev.name as name,
                dev.email as email,
                dev.expertise_areas as expertise_areas,
                dev.total_commits as total_commits,
                dev.contribution_score as contribution_score,
                dev.lines_added as lines_added,
                dev.lines_removed as lines_removed
            ORDER BY dev.contribution_score DESC
            LIMIT 5
            """
            queries.append(("relevant_developers", developer_query))
        
        # Query 3: Get files and their modification patterns
        if 'file' in keywords['node_types'] or keywords['search_terms']:
            file_terms = keywords['search_terms'] if keywords['search_terms'] else ['']
            file_pattern = '|'.join(file_terms) if file_terms != [''] else '.*'
            file_query = f"""
            MATCH (c:Codebase {{id: $codebase_id}})
            -[:CONTAINS_COMMIT]->(commit:Commit)
            -[:MODIFIES]->(file:File)
            WHERE file.name =~ '(?i).*({file_pattern}).*'
               OR file.path =~ '(?i).*({file_pattern}).*'
            RETURN 
                file.name as filename,
                file.path as filepath,
                file.extension as extension,
                file.total_commits as modifications,
                collect(DISTINCT commit.sha)[0..3] as recent_commits
            ORDER BY file.total_commits DESC
            LIMIT 5
            """
            queries.append(("relevant_files", file_query))
        
        # Query 4: Get milestones and releases
        if 'milestone' in keywords['node_types'] or any(term in keywords['search_terms'] for term in ['release', 'version', 'milestone']):
            milestone_query = f"""
            {base_query}
            -[:HAS_MILESTONE]->(milestone:BusinessMilestone)
            OPTIONAL MATCH (milestone)-[:RELATES_TO]->(commit:Commit)
            RETURN 
                milestone.name as name,
                milestone.description as description,
                milestone.milestone_type as type,
                milestone.version as version,
                milestone.date as date,
                collect(DISTINCT commit.sha)[0..3] as related_commits
            ORDER BY milestone.date DESC
            LIMIT 3
            """
            queries.append(("relevant_milestones", milestone_query))
        
        # Query 5: Get collaboration patterns (who works with whom)
        if any(word in keywords['search_terms'] for word in ['collaboration', 'team', 'together', 'with']):
            collab_query = f"""
            {base_query}
            -[:CONTAINS_COMMIT]->(commit:Commit)
            <-[:AUTHORED]-(dev1:Developer)
            WITH c, collect(DISTINCT dev1) as developers
            UNWIND developers as dev1
            UNWIND developers as dev2
            WHERE dev1 <> dev2
            MATCH (dev1)-[:AUTHORED]->(c1:Commit)<-[:CONTAINS_COMMIT]-(c)
            MATCH (dev2)-[:AUTHORED]->(c2:Commit)<-[:CONTAINS_COMMIT]-(c)
            MATCH (c1)-[:MODIFIES]->(f:File)<-[:MODIFIES]-(c2)
            RETURN 
                dev1.name as developer1,
                dev2.name as developer2,
                count(DISTINCT f) as shared_files,
                collect(DISTINCT f.name)[0..3] as common_files
            ORDER BY shared_files DESC
            LIMIT 5
            """
            queries.append(("collaboration_patterns", collab_query))
        
        # Default fallback query - get general repository overview
        if not queries:
            overview_query = f"""
            {base_query}
            OPTIONAL MATCH (c)-[:CONTAINS_COMMIT]->(recent_commit:Commit)
            OPTIONAL MATCH (c)-[:HAS_MILESTONE]->(milestone:BusinessMilestone)
            OPTIONAL MATCH (recent_commit)<-[:AUTHORED]-(dev:Developer)
            RETURN 
                c.name as codebase_name,
                c.total_commits as total_commits,
                c.total_developers as total_developers,
                collect(DISTINCT recent_commit.message)[0..3] as recent_messages,
                collect(DISTINCT dev.name)[0..5] as active_developers,
                collect(DISTINCT milestone.name)[0..3] as milestones
            """
            queries.append(("repository_overview", overview_query))
        
        return queries

    def execute_context_queries(self, codebase_id: str, queries: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Execute the context-gathering queries"""
        context = {}
        
        with self.neo4j_service.driver.session() as session:
            for query_name, query in queries:
                try:
                    result = session.run(query, codebase_id=codebase_id)
                    records = [serialize_neo4j_value(dict(record)) for record in result]
                    context[query_name] = records
                    logger.info(f"Context query '{query_name}' returned {len(records)} results")
                except Exception as e:
                    logger.error(f"Failed to execute context query '{query_name}': {str(e)}")
                    context[query_name] = []
        
        return context

    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format the gathered context for the LLM prompt"""
        formatted_context = "REPOSITORY CONTEXT:\n\n"
        
        # Format commits
        if 'relevant_commits' in context and context['relevant_commits']:
            formatted_context += "=== RELEVANT COMMITS ===\n"
            for commit in context['relevant_commits']:
                formatted_context += f"• Commit {commit.get('commit_sha', 'N/A')[:8]} by {commit.get('author_name', 'Unknown')}\n"
                formatted_context += f"  Message: {commit.get('commit_message', 'N/A')}\n"
                if commit.get('feature_summary'):
                    formatted_context += f"  Summary: {commit['feature_summary']}\n"
                if commit.get('business_impact'):
                    formatted_context += f"  Impact: {commit['business_impact']}\n"
                if commit.get('files_modified'):
                    formatted_context += f"  Files: {', '.join(commit['files_modified'][:3])}\n"
                formatted_context += "\n"
        
        # Format developers
        if 'relevant_developers' in context and context['relevant_developers']:
            formatted_context += "=== RELEVANT DEVELOPERS ===\n"
            for dev in context['relevant_developers']:
                formatted_context += f"• {dev.get('name', 'N/A')} ({dev.get('email', 'N/A')})\n"
                formatted_context += f"  Commits: {dev.get('total_commits', 0)}, Score: {dev.get('contribution_score', 0)}\n"
                if dev.get('expertise_areas'):
                    formatted_context += f"  Expertise: {', '.join(dev['expertise_areas'])}\n"
                formatted_context += "\n"
        
        # Format files
        if 'relevant_files' in context and context['relevant_files']:
            formatted_context += "=== RELEVANT FILES ===\n"
            for file in context['relevant_files']:
                formatted_context += f"• {file.get('filename', 'N/A')} ({file.get('extension', 'N/A')})\n"
                formatted_context += f"  Path: {file.get('filepath', 'N/A')}\n"
                formatted_context += f"  Modifications: {file.get('modifications', 0)}\n"
                formatted_context += "\n"
        
        # Format milestones
        if 'relevant_milestones' in context and context['relevant_milestones']:
            formatted_context += "=== RELEVANT MILESTONES ===\n"
            for milestone in context['relevant_milestones']:
                formatted_context += f"• {milestone.get('name', 'N/A')} ({milestone.get('type', 'N/A')})\n"
                formatted_context += f"  Description: {milestone.get('description', 'N/A')}\n"
                if milestone.get('version'):
                    formatted_context += f"  Version: {milestone['version']}\n"
                formatted_context += "\n"
        
        # Format collaboration patterns
        if 'collaboration_patterns' in context and context['collaboration_patterns']:
            formatted_context += "=== COLLABORATION PATTERNS ===\n"
            for collab in context['collaboration_patterns']:
                formatted_context += f"• {collab.get('developer1', 'N/A')} collaborates with {collab.get('developer2', 'N/A')}\n"
                formatted_context += f"  Shared files: {collab.get('shared_files', 0)}\n"
                if collab.get('common_files'):
                    formatted_context += f"  Common files: {', '.join(collab['common_files'])}\n"
                formatted_context += "\n"
        
        # Format repository overview
        if 'repository_overview' in context and context['repository_overview']:
            overview = context['repository_overview'][0] if context['repository_overview'] else {}
            formatted_context += "=== REPOSITORY OVERVIEW ===\n"
            formatted_context += f"• Repository: {overview.get('codebase_name', 'N/A')}\n"
            formatted_context += f"• Total commits: {overview.get('total_commits', 0)}\n"
            formatted_context += f"• Total developers: {overview.get('total_developers', 0)}\n"
            if overview.get('active_developers'):
                formatted_context += f"• Active developers: {', '.join(overview['active_developers'])}\n"
            if overview.get('milestones'):
                formatted_context += f"• Milestones: {', '.join(overview['milestones'])}\n"
            formatted_context += "\n"
        
        return formatted_context

    def generate_llm_response(self, user_query: str, context: str, conversation_history: List[Dict[str, str]]) -> str:
        """Generate response using LLM with the gathered context"""
        if not self.analysis_service.client:
            return f"Based on the repository data: {context}\n\nRegarding your question '{user_query}', I can see the relevant information above, but I don't have LLM capabilities configured to provide a detailed analysis."
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\nPREVIOUS CONVERSATION:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')[:200]  # Truncate long messages
                conversation_context += f"{role.upper()}: {content}\n"
            conversation_context += "\n"
        
        system_prompt = """You are an AI assistant specialized in analyzing software repositories and Git history. You have access to detailed information about commits, developers, files, and collaboration patterns from a Neo4j graph database.

Your role is to:
1. Answer questions about the codebase using the provided context
2. Explain development patterns and trends
3. Identify key contributors and their expertise areas
4. Describe the evolution of features and bug fixes
5. Provide insights about collaboration and code quality

Always base your answers on the provided repository context. Be specific and reference actual commits, developers, and files when possible."""

        user_prompt = f"""Context from repository analysis:
{context}

{conversation_context}

User Question: {user_query}

Please provide a helpful and detailed answer based on the repository context provided above. Reference specific commits, developers, files, or patterns when relevant to the question."""

        try:
            response = self.analysis_service.client.chat.completions.create(
                model=self.analysis_service.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=500
            )
            
            response_content = response.choices[0].message.content
            if not response_content or response_content.strip() == "":
                logger.warning("LLM returned empty response")
                return f"Based on the repository analysis:\n\n{context}\n\nI found the above information relevant to your question, but the LLM response was empty."
            
            return response_content.strip()
        except Exception as e:
            logger.error(f"LLM response generation failed: {str(e)}")
            return f"I found relevant information in the repository, but encountered an error generating a detailed response. Here's what I found:\n\n{context}"

    def chat_with_codebase(self, codebase_id: str, user_query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Main chat function that orchestrates the entire process"""
        if conversation_history is None:
            conversation_history = []
        
        logger.info(f"Processing chat query for codebase {codebase_id}: {user_query[:100]}...")
        
        # Step 1: Extract keywords from user query
        keywords = self.extract_keywords_from_query(user_query)
        logger.info(f"Extracted keywords: {keywords}")
        
        # Step 2: Build context-gathering Cypher queries
        queries = self.build_context_cypher_queries(codebase_id, keywords)
        logger.info(f"Built {len(queries)} context queries")
        
        # Step 3: Execute queries and gather context
        context = self.execute_context_queries(codebase_id, queries)
        
        # Step 4: Format context for LLM
        formatted_context = self.format_context_for_llm(context)
        
        # Step 5: Generate LLM response
        response = self.generate_llm_response(user_query, formatted_context, conversation_history)
        
        # Step 6: Prepare response data
        relevant_nodes = []
        for query_name, results in context.items():
            for result in results:
                relevant_nodes.append({
                    "type": query_name,
                    "data": result
                })
        
        return {
            "response": response,
            "context": context,
            "relevant_nodes": relevant_nodes[:10],  # Limit to top 10 most relevant
            "cypher_queries_used": [query for _, query in queries],
            "keywords_extracted": keywords
        }