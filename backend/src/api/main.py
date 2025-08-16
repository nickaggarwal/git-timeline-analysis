from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime

from src.models.schema import AnalysisRequest, ChatQuery, ChatRequest, ChatResponse
from src.services.codebase_analyzer import CodebaseAnalyzer
from src.services.chat_service import ChatService
from src.services.neo4j_service import serialize_neo4j_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Codebase Time Machine API",
    description="Analyze Git repositories and build knowledge graphs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analyzer instance
analyzer = None

def get_analyzer():
    """Get or create the CodebaseAnalyzer instance"""
    global analyzer
    if analyzer is None:
        # Get configuration from environment or use defaults
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        analyzer = CodebaseAnalyzer(
            neo4j_uri=neo4j_uri,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            openai_api_key=openai_api_key
        )
    return analyzer

# Pydantic models for API
class AnalyzeRepoResponse(BaseModel):
    status: str
    codebase_id: str
    message: str
    analysis_summary: Optional[Dict[str, Any]] = None


# Store for background tasks (in production, use Redis or similar)
analysis_jobs = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Codebase Time Machine API", 
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        analyzer_instance = get_analyzer()
        neo4j_healthy = analyzer_instance.neo4j_service.test_connection()
        
        return {
            "status": "healthy" if neo4j_healthy else "degraded",
            "neo4j_connection": "ok" if neo4j_healthy else "failed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/analyze", response_model=AnalyzeRepoResponse)
async def analyze_repository(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start repository analysis"""
    
    try:
        git_url = str(request.git_url)
        codebase_id = git_url.split('/')[-1].replace('.git', '')
        
        # Create analysis request
        analysis_request = AnalysisRequest(
            git_url=request.git_url,
            include_llm_analysis=request.include_llm_analysis
        )
        
        # Start analysis in background
        job_id = f"{codebase_id}_{int(datetime.now().timestamp())}"
        analysis_jobs[job_id] = {
            "status": "running",
            "codebase_id": codebase_id,
            "started_at": datetime.now().isoformat(),
            "progress": "Initializing analysis..."
        }
        
        background_tasks.add_task(run_analysis, job_id, analysis_request)
        
        return AnalyzeRepoResponse(
            status="started",
            codebase_id=codebase_id,
            message=f"Analysis started for {git_url}. Use /status/{job_id} to check progress.",
            analysis_summary={"job_id": job_id}
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

async def run_analysis(job_id: str, request: AnalysisRequest):
    """Run the analysis in background"""
    try:
        analyzer_instance = get_analyzer()
        
        # Update job status
        analysis_jobs[job_id]["progress"] = "Cloning repository..."
        
        # Run the analysis
        result = analyzer_instance.analyze_repository(request)
        
        # Update job with results
        analysis_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result,
            "progress": "Analysis completed successfully"
        })
        
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {str(e)}")
        analysis_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
            "progress": f"Analysis failed: {str(e)}"
        })

@app.get("/status/{job_id}")
async def get_analysis_status(job_id: str):
    """Get analysis job status"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return analysis_jobs[job_id]

@app.get("/codebase/{codebase_id}/summary")
async def get_codebase_summary(codebase_id: str):
    """Get codebase summary from Neo4j"""
    try:
        analyzer_instance = get_analyzer()
        summary = analyzer_instance.get_codebase_summary(codebase_id)
        return summary
    except Exception as e:
        logger.error(f"Failed to get summary for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebase/{codebase_id}/graph")
async def get_graph_data(codebase_id: str):
    """Get graph visualization data"""
    try:
        analyzer_instance = get_analyzer()
        graph_data = analyzer_instance.neo4j_service.get_commit_graph_data(codebase_id)
        return graph_data
    except Exception as e:
        logger.error(f"Failed to get graph data for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebase/{codebase_id}/developers")
async def get_developer_data(codebase_id: str):
    """Get developer expertise and contribution data"""
    try:
        analyzer_instance = get_analyzer()
        developer_data = analyzer_instance.neo4j_service.get_developer_expertise_data(codebase_id)
        return {"developers": developer_data}
    except Exception as e:
        logger.error(f"Failed to get developer data for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebase/{codebase_id}/timeline")
async def get_timeline_data(codebase_id: str):
    """Get timeline of commits and milestones"""
    try:
        analyzer_instance = get_analyzer()
        
        # Get recent commits
        with analyzer_instance.neo4j_service.driver.session() as session:
            commits_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                OPTIONAL MATCH (commit)<-[:AUTHORED]-(dev:Developer)
                RETURN commit.sha as sha,
                       commit.message as message,
                       commit.timestamp as timestamp,
                       commit.feature_summary as feature_summary,
                       commit.business_impact as business_impact,
                       dev.name as author_name
                ORDER BY commit.timestamp DESC
                LIMIT 50
            """, codebase_id=codebase_id)
            
            commits = [serialize_neo4j_value(dict(record)) for record in commits_result]
            
            # Get milestones
            milestones_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:HAS_MILESTONE]->(milestone:BusinessMilestone)
                RETURN milestone.name as name,
                       milestone.description as description,
                       milestone.date as date,
                       milestone.milestone_type as type,
                       milestone.version as version
                ORDER BY milestone.date DESC
            """, codebase_id=codebase_id)
            
            milestones = [serialize_neo4j_value(dict(record)) for record in milestones_result]
        
        return {
            "commits": commits,
            "milestones": milestones
        }
        
    except Exception as e:
        logger.error(f"Failed to get timeline data for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebase/{codebase_id}/business-timeline")
async def get_business_timeline(codebase_id: str):
    """Get business timeline with monthly summaries and milestones"""
    try:
        analyzer_instance = get_analyzer()
        
        with analyzer_instance.neo4j_service.driver.session() as session:
            # Get all commits for monthly aggregation
            commits_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                OPTIONAL MATCH (commit)<-[:AUTHORED]-(dev:Developer)
                RETURN commit.sha as sha,
                       commit.message as message,
                       commit.timestamp as timestamp,
                       commit.feature_summary as feature_summary,
                       commit.business_impact as business_impact,
                       commit.insertions as insertions,
                       commit.deletions as deletions,
                       dev.name as author_name,
                       dev.email as author_email
                ORDER BY commit.timestamp DESC
            """, codebase_id=codebase_id)
            
            commits = [serialize_neo4j_value(dict(record)) for record in commits_result]
            
            # Get business milestones
            milestones_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:HAS_MILESTONE]->(milestone:BusinessMilestone)
                RETURN milestone.id as id,
                       milestone.name as name,
                       milestone.description as description,
                       milestone.date as date,
                       milestone.milestone_type as type,
                       milestone.version as version,
                       milestone.related_commits as related_commits
                ORDER BY milestone.date DESC
            """, codebase_id=codebase_id)
            
            milestones = [serialize_neo4j_value(dict(record)) for record in milestones_result]
            
            # Generate monthly business summaries
            monthly_summaries = []
            if commits:
                from datetime import datetime, timedelta
                from collections import defaultdict
                import calendar
                
                monthly_data = defaultdict(lambda: {
                    'commits': [],
                    'total_commits': 0,
                    'unique_authors': set(),
                    'insertions': 0,
                    'deletions': 0,
                    'business_impacts': [],
                    'features_added': [],
                    'bugs_fixed': [],
                    'performance_improvements': [],
                    'milestones': []
                })
                
                # Group commits by month
                for commit in commits:
                    if commit.get('timestamp'):
                        try:
                            # Handle Neo4j DateTime object
                            timestamp = commit['timestamp']
                            if hasattr(timestamp, 'to_native'):
                                commit_date = timestamp.to_native()
                            elif isinstance(timestamp, str):
                                commit_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                commit_date = timestamp
                            
                            month_key = f"{commit_date.year}-{commit_date.month:02d}"
                            month_name = f"{calendar.month_name[commit_date.month]} {commit_date.year}"
                            
                            monthly_data[month_key]['month_name'] = month_name
                            monthly_data[month_key]['year'] = commit_date.year
                            monthly_data[month_key]['month'] = commit_date.month
                            monthly_data[month_key]['commits'].append(commit)
                            monthly_data[month_key]['total_commits'] += 1
                            
                            if commit.get('author_name'):
                                monthly_data[month_key]['unique_authors'].add(commit['author_name'])
                            
                            if commit.get('insertions'):
                                monthly_data[month_key]['insertions'] += commit['insertions']
                            if commit.get('deletions'):
                                monthly_data[month_key]['deletions'] += commit['deletions']
                            
                            # Categorize business impact
                            if commit.get('business_impact'):
                                impact = commit['business_impact'].lower()
                                monthly_data[month_key]['business_impacts'].append(commit['business_impact'])
                                
                                if 'feature' in impact or 'enhancement' in impact:
                                    monthly_data[month_key]['features_added'].append(commit['message'].split('\n')[0][:100])
                                elif 'bug' in impact or 'fix' in impact:
                                    monthly_data[month_key]['bugs_fixed'].append(commit['message'].split('\n')[0][:100])
                                elif 'performance' in impact or 'optimization' in impact:
                                    monthly_data[month_key]['performance_improvements'].append(commit['message'].split('\n')[0][:100])
                        except Exception as e:
                            logger.warning(f"Error processing commit timestamp: {e}")
                            continue
                
                # Add milestones to monthly data
                for milestone in milestones:
                    if milestone.get('date'):
                        try:
                            # Handle Neo4j DateTime object
                            milestone_date = milestone['date']
                            if hasattr(milestone_date, 'to_native'):
                                milestone_date = milestone_date.to_native()
                            elif isinstance(milestone_date, str):
                                milestone_date = datetime.fromisoformat(milestone_date.replace('Z', '+00:00'))
                            
                            month_key = f"{milestone_date.year}-{milestone_date.month:02d}"
                            if month_key in monthly_data:
                                monthly_data[month_key]['milestones'].append(milestone)
                        except Exception as e:
                            logger.warning(f"Error processing milestone date: {e}")
                            continue
                
                # Convert to list and sort by date
                for month_key, data in monthly_data.items():
                    data['unique_authors'] = list(data['unique_authors'])
                    monthly_summaries.append({
                        'month_key': month_key,
                        'month_name': data['month_name'],
                        'year': data['year'],
                        'month': data['month'],
                        'total_commits': data['total_commits'],
                        'unique_authors': data['unique_authors'],
                        'author_count': len(data['unique_authors']),
                        'insertions': data['insertions'],
                        'deletions': data['deletions'],
                        'net_changes': data['insertions'] - data['deletions'],
                        'business_impacts': list(set(data['business_impacts']))[:10],  # Unique impacts, limited
                        'features_added': data['features_added'][:5],  # Top 5 features
                        'bugs_fixed': data['bugs_fixed'][:5],  # Top 5 bug fixes
                        'performance_improvements': data['performance_improvements'][:3],  # Top 3 improvements
                        'milestones': data['milestones'],
                        'milestone_count': len(data['milestones']),
                        'top_commits': sorted(data['commits'], 
                                            key=lambda x: (x.get('insertions', 0) + x.get('deletions', 0)), 
                                            reverse=True)[:3]  # Top 3 commits by size
                    })
                
                # Sort by year and month descending
                monthly_summaries.sort(key=lambda x: (x['year'], x['month']), reverse=True)
        
        return {
            "monthly_summaries": monthly_summaries,
            "milestones": milestones,
            "total_months": len(monthly_summaries),
            "total_milestones": len(milestones),
            "total_commits": len(commits)
        }
        
    except Exception as e:
        logger.error(f"Failed to get business timeline for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebase/{codebase_id}/ai-summary")
async def get_ai_summary(codebase_id: str):
    """Get AI-powered summary with heatmap, top developers, and recent business updates"""
    try:
        analyzer_instance = get_analyzer()
        
        with analyzer_instance.neo4j_service.driver.session() as session:
            # Get all commits for comprehensive analysis
            commits_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:CONTAINS_COMMIT]->(commit:Commit)
                OPTIONAL MATCH (commit)<-[:AUTHORED]-(dev:Developer)
                RETURN commit.sha as sha,
                       commit.message as message,
                       commit.timestamp as timestamp,
                       commit.feature_summary as feature_summary,
                       commit.business_impact as business_impact,
                       commit.insertions as insertions,
                       commit.deletions as deletions,
                       dev.name as author_name,
                       dev.email as author_email
                ORDER BY commit.timestamp DESC
            """, codebase_id=codebase_id)
            
            commits = [serialize_neo4j_value(dict(record)) for record in commits_result]
            
            # Get top developers
            developers_result = session.run("""
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
                LIMIT 3
            """, codebase_id=codebase_id)
            
            top_developers = [serialize_neo4j_value(dict(record)) for record in developers_result]
            
            # Get business milestones
            milestones_result = session.run("""
                MATCH (c:Codebase {id: $codebase_id})-[:HAS_MILESTONE]->(milestone:BusinessMilestone)
                RETURN milestone.id as id,
                       milestone.name as name,
                       milestone.description as description,
                       milestone.date as date,
                       milestone.milestone_type as type,
                       milestone.version as version
                ORDER BY milestone.date DESC
            """, codebase_id=codebase_id)
            
            milestones = [serialize_neo4j_value(dict(record)) for record in milestones_result]
            
            # Process data for AI summary
            from datetime import datetime, timedelta
            from collections import defaultdict
            import calendar
            
            # Generate activity heatmap (last 12 months)
            monthly_activity = defaultdict(int)
            recent_commits = []
            from datetime import timezone
            now = datetime.now(timezone.utc)
            two_months_ago = now - timedelta(days=60)
            
            for commit in commits:
                if commit.get('timestamp'):
                    try:
                        timestamp = commit['timestamp']
                        if hasattr(timestamp, 'to_native'):
                            commit_date = timestamp.to_native()
                            if commit_date.tzinfo is None:
                                commit_date = commit_date.replace(tzinfo=timezone.utc)
                        elif isinstance(timestamp, str):
                            commit_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            commit_date = timestamp
                            if commit_date.tzinfo is None:
                                commit_date = commit_date.replace(tzinfo=timezone.utc)
                        
                        # For heatmap
                        month_key = f"{commit_date.year}-{commit_date.month:02d}"
                        monthly_activity[month_key] += 1
                        
                        # For recent activity
                        if commit_date >= two_months_ago:
                            recent_commits.append(commit)
                    except Exception as e:
                        logger.warning(f"Error processing commit timestamp: {e}")
                        continue
            
            # Generate 12-month heatmap
            heatmap_data = []
            start_date = now - timedelta(days=365)
            for i in range(12):
                date = start_date + timedelta(days=i*30)
                month_key = f"{date.year}-{date.month:02d}"
                commit_count = monthly_activity.get(month_key, 0)
                heatmap_data.append({
                    'month': date.strftime('%b %y'),
                    'month_key': month_key,
                    'commit_count': commit_count,
                    'activity_level': 'high' if commit_count > 10 else 'medium' if commit_count > 5 else 'low'
                })
            
            # Recent business insights (last 2 months)
            recent_business_data = defaultdict(lambda: {
                'commits': [],
                'features_added': [],
                'bugs_fixed': [],
                'performance_improvements': [],
                'milestones': []
            })
            
            for commit in recent_commits:
                if commit.get('timestamp'):
                    try:
                        timestamp = commit['timestamp']
                        if hasattr(timestamp, 'to_native'):
                            commit_date = timestamp.to_native()
                            if commit_date.tzinfo is None:
                                commit_date = commit_date.replace(tzinfo=timezone.utc)
                        elif isinstance(timestamp, str):
                            commit_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            commit_date = timestamp
                            if commit_date.tzinfo is None:
                                commit_date = commit_date.replace(tzinfo=timezone.utc)
                        
                        month_key = f"{commit_date.year}-{commit_date.month:02d}"
                        month_name = f"{calendar.month_name[commit_date.month]} {commit_date.year}"
                        
                        recent_business_data[month_key]['month_name'] = month_name
                        recent_business_data[month_key]['commits'].append(commit)
                        
                        # Categorize business impact
                        if commit.get('business_impact'):
                            impact = commit['business_impact'].lower()
                            if 'feature' in impact or 'enhancement' in impact:
                                recent_business_data[month_key]['features_added'].append(commit['message'].split('\n')[0][:80])
                            elif 'bug' in impact or 'fix' in impact:
                                recent_business_data[month_key]['bugs_fixed'].append(commit['message'].split('\n')[0][:80])
                            elif 'performance' in impact or 'optimization' in impact:
                                recent_business_data[month_key]['performance_improvements'].append(commit['message'].split('\n')[0][:80])
                    except Exception as e:
                        logger.warning(f"Error processing recent commit: {e}")
                        continue
            
            # Add recent milestones
            for milestone in milestones:
                if milestone.get('date'):
                    try:
                        milestone_date = milestone['date']
                        if hasattr(milestone_date, 'to_native'):
                            milestone_date = milestone_date.to_native()
                            if milestone_date.tzinfo is None:
                                milestone_date = milestone_date.replace(tzinfo=timezone.utc)
                        elif isinstance(milestone_date, str):
                            milestone_date = datetime.fromisoformat(milestone_date.replace('Z', '+00:00'))
                        
                        if milestone_date >= two_months_ago:
                            month_key = f"{milestone_date.year}-{milestone_date.month:02d}"
                            if month_key in recent_business_data:
                                recent_business_data[month_key]['milestones'].append(milestone)
                    except Exception as e:
                        logger.warning(f"Error processing recent milestone: {e}")
                        continue
            
            # Convert recent business data to list
            recent_business_updates = []
            for month_key, data in recent_business_data.items():
                if data.get('month_name'):
                    recent_business_updates.append({
                        'month_key': month_key,
                        'month_name': data['month_name'],
                        'total_commits': len(data['commits']),
                        'features_added': data['features_added'][:3],
                        'bugs_fixed': data['bugs_fixed'][:3],
                        'performance_improvements': data['performance_improvements'][:2],
                        'milestones': data['milestones'],
                        'top_commits': sorted(data['commits'], 
                                            key=lambda x: (x.get('insertions', 0) + x.get('deletions', 0)), 
                                            reverse=True)[:2]
                    })
            
            # Sort recent updates by month descending
            recent_business_updates.sort(key=lambda x: x['month_key'], reverse=True)
            
            # Generate AI insights using LLM if available
            ai_insights = None
            if analyzer_instance.analysis_service.client:
                try:
                    # Create context for AI analysis
                    context = f"""
                    Repository Analysis Summary:
                    - Total commits in last 2 months: {len(recent_commits)}
                    - Top 3 contributors: {', '.join([dev['name'] for dev in top_developers])}
                    - Recent milestones: {len([m for m in milestones if m.get('date')])} total milestones
                    - Activity pattern: {'High activity' if len(recent_commits) > 20 else 'Medium activity' if len(recent_commits) > 10 else 'Low activity'}
                    """
                    
                    # Generate AI summary
                    response = analyzer_instance.analysis_service.client.chat.completions.create(
                        model=analyzer_instance.analysis_service.deployment_name,
                        messages=[{
                            "role": "user",
                            "content": f"Based on this repository data, provide 3-4 key insights about the development activity and team productivity in 2-3 sentences each: {context}"
                        }],
                        max_completion_tokens=400
                    )
                    
                    ai_insights = response.choices[0].message.content if response.choices else None
                except Exception as e:
                    logger.warning(f"Failed to generate AI insights: {e}")
                    ai_insights = None
        
        return {
            "heatmap_data": heatmap_data,
            "top_developers": top_developers,
            "recent_business_updates": recent_business_updates[:2],  # Last 2 months
            "ai_insights": ai_insights,
            "summary_stats": {
                "total_commits": len(commits),
                "recent_commits": len(recent_commits),
                "total_developers": len(top_developers),
                "total_milestones": len(milestones),
                "activity_trend": "increasing" if len(recent_commits) > 10 else "stable"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI summary for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebase/{codebase_id}/collaboration")
async def get_collaboration_data(codebase_id: str):
    """Get developer collaboration patterns"""
    try:
        analyzer_instance = get_analyzer()
        collaboration_data = analyzer_instance.get_developer_collaboration_patterns(codebase_id)
        return collaboration_data
    except Exception as e:
        logger.error(f"Failed to get collaboration data for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/codebase/{codebase_id}/chat")
async def chat_with_codebase(codebase_id: str, request: ChatRequest):
    """Enhanced chat with codebase using Cypher queries and LLM"""
    try:
        analyzer_instance = get_analyzer()
        
        # Create enhanced chat service
        chat_service = ChatService(
            neo4j_service=analyzer_instance.neo4j_service,
            analysis_service=analyzer_instance.analysis_service
        )
        
        # Process the chat query with intelligent context gathering
        result = chat_service.chat_with_codebase(
            codebase_id=codebase_id,
            user_query=request.message,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            response=result["response"],
            context=result["context"],
            relevant_nodes=result["relevant_nodes"],
            cypher_queries_used=result["cypher_queries_used"]
        )
        
    except Exception as e:
        logger.error(f"Enhanced chat failed for {codebase_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/codebases")
async def list_codebases():
    """List all analyzed codebases"""
    try:
        analyzer_instance = get_analyzer()
        
        with analyzer_instance.neo4j_service.driver.session() as session:
            result = session.run("""
                MATCH (c:Codebase)
                RETURN c.id as id,
                       c.name as name,
                       c.git_url as git_url,
                       c.last_analyzed as last_analyzed,
                       c.total_commits as total_commits,
                       c.total_developers as total_developers,
                       c.primary_language as primary_language
                ORDER BY c.last_analyzed DESC
            """)
            
            codebases = [dict(record) for record in result]
        
        return codebases
        
    except Exception as e:
        logger.error(f"Failed to list codebases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)