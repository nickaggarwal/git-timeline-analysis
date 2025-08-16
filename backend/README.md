# Codebase Time Machine - Backend

This is the backend service for the Codebase Time Machine project. It analyzes Git repositories and builds a knowledge graph in Neo4j.

## Prerequisites

1. **Python 3.8+**
2. **Neo4j Database** (running on localhost:7687)
3. **Git** (for repository cloning)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Neo4j database:
   - Download Neo4j Desktop or use Docker:
   ```bash
   docker run --name neo4j -p7474:7474 -p7687:7687 -d -v neo4j_data:/data -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your actual configurations
```

## Testing the Pipeline

Run the test script to verify everything works:

```bash
cd backend
python test_analysis.py
```

This will:
1. Clone a small test repository (Hello-World)
2. Analyze commits, developers, and file changes  
3. Dump all data into Neo4j as a graph
4. Verify the graph was created successfully

## Project Structure

```
backend/
├── src/
│   ├── models/
│   │   └── schema.py          # Pydantic data models
│   ├── services/
│   │   ├── git_service.py     # Git repository analysis
│   │   ├── analysis_service.py # LLM-powered commit analysis
│   │   ├── neo4j_service.py   # Neo4j graph operations
│   │   └── codebase_analyzer.py # Main orchestration service
│   └── api/                   # FastAPI endpoints (future)
├── test_analysis.py          # Test script
├── requirements.txt
└── README.md
```

## Data Model

The system creates a Neo4j graph with the following node types:

- **Codebase**: Repository metadata
- **Commit**: Individual commits with LLM analysis
- **Developer**: Contributor information and expertise areas
- **Branch**: Repository branches  
- **File**: Files touched by commits
- **BusinessMilestone**: Important releases/features

## Relationships

- `(Developer)-[:AUTHORED]->(Commit)`
- `(Commit)-[:PARENT_OF]->(Commit)` 
- `(Commit)-[:MODIFIES]->(File)`
- `(Codebase)-[:CONTAINS_COMMIT]->(Commit)`
- `(Codebase)-[:HAS_BRANCH]->(Branch)`
- `(BusinessMilestone)-[:RELATES_TO]->(Commit)`

## Key Features

- ✅ Git repository cloning and analysis
- ✅ Commit history extraction with metadata
- ✅ Developer expertise area detection
- ✅ LLM-powered feature summarization
- ✅ Business milestone identification
- ✅ Neo4j graph construction
- ✅ File change tracking and relationships

## Next Steps

After reaching the Neo4j checkpoint, the next phase will include:
- Frontend dashboard development
- Chat interface for querying the graph
- Advanced visualizations
- Real-time analysis updates