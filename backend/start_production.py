#!/usr/bin/env python3

"""
Codebase Time Machine - Production Server Startup
This script starts the FastAPI backend using Gunicorn with optimal production settings
"""

import os
import sys
import subprocess
import multiprocessing
from pathlib import Path

def main():
    # Get script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting Codebase Time Machine API Server (Production Mode)")
    print("=" * 60)
    
    # Check if virtual environment exists
    venv_path = script_dir / "venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run setup first.")
        sys.exit(1)
    
    # Check if gunicorn is installed
    gunicorn_path = venv_path / "bin" / "gunicorn"
    if not gunicorn_path.exists():
        print("❌ Gunicorn not found. Installing...")
        subprocess.run([
            str(venv_path / "bin" / "pip"), 
            "install", "-r", "requirements.txt"
        ], check=True)
    
    # Ensure logs directory exists
    logs_dir = script_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Clear log files
    (logs_dir / "access.log").touch()
    (logs_dir / "error.log").touch()
    
    # Calculate optimal worker count
    worker_count = multiprocessing.cpu_count() * 2 + 1
    
    print(f"📊 Configuration:")
    print(f"   - Workers: {worker_count}")
    print(f"   - Worker Class: uvicorn.workers.UvicornWorker")
    print(f"   - Bind Address: 0.0.0.0:8001")
    print(f"   - Timeout: 120s")
    print(f"   - Max Requests: 1000")
    print()
    
    # Load environment variables
    env_file = script_dir.parent / ".env"
    if env_file.exists():
        import dotenv
        dotenv.load_dotenv(env_file)
        print("✅ Loaded environment variables from .env")
    else:
        print("⚠️  Warning: .env file not found")
    
    # Gunicorn command
    cmd = [
        str(gunicorn_path),
        "--config", str(script_dir / "gunicorn.conf.py"),
        "src.main:app"
    ]
    
    print("🎯 Starting Gunicorn...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        # Execute gunicorn
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()