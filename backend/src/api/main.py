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