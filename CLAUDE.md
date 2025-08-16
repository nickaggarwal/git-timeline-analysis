# Codebase Time Machine - Claude Context

## System Status
- Neo4j Desktop is running at neo4j://127.0.0.1:7687 (PID: 21254)
- Database contains existing analysis data:
  - 135 total nodes (70 Files, 43 Commits, 8 Developers, 8 Business Milestones, 4 Branches, 2 Codebases)
  - 332 total relationships
  - Analyzed codebases: triton-co-pilot and langsmith-mcp-server

## How to Start the System
```bash
cd /Users/nilesh/first-project
./start_system.sh
```

## Project Structure
- Backend: FastAPI server (runs on port 8001)
- Frontend: Next.js application (runs on port 3000) 
- Database: Neo4j (ports 7474 for web UI, 7687 for bolt connection)

## Key Commands
- Check Neo4j data: `cd backend && python3 check_neo4j_data.py`
- Start system: `./start_system.sh`

## Current Status (Fixed)
✅ **Timeline functionality**: Fixed timestamp serialization - now shows proper ISO format dates
✅ **Chat API**: Fixed OpenAI client errors and parameter issues
✅ **Developer Scorecards**: Fixed dashboard integration - now shows developer data
⚠️ **Chat LLM responses**: API calls successful but Azure OpenAI o4-mini model returns empty responses
- Context gathering works correctly (finds relevant commits, developers, files)
- API calls return HTTP 200 but response content is empty
- Fallback provides relevant repository context when LLM fails

## Endpoints Working
- GET `/codebases` - Lists all analyzed codebases ✅
- GET `/codebase/{id}/timeline` - Returns commits with proper timestamps ✅  
- GET `/codebase/{id}/developers` - Returns developer scorecard data ✅
- POST `/codebase/{id}/chat` - Returns context + attempts LLM response ⚠️

## Dashboard Features
✅ **Previous Analyses**: Shows on homepage with clickable cards
✅ **Timeline Tab**: Displays commits with timestamps and summaries
✅ **Developer Tab**: Shows comprehensive scorecards with metrics and rankings
⚠️ **Chat Tab**: Interface works but LLM responses are empty (fallback shows context)
🔧 **Graph Tab**: Placeholder - needs implementation