# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = os.path.join(os.path.dirname(__file__), "logs", "access.log")
errorlog = os.path.join(os.path.dirname(__file__), "logs", "error.log")
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'codebase-time-machine-api'

# Server mechanics
daemon = False
pidfile = os.path.join(os.path.dirname(__file__), "logs", "gunicorn.pid")
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
# keyfile = None
# certfile = None

# Worker recycling
preload_app = True
lazy_apps = False

# Performance tuning
# Use RAM for worker temp files - platform specific
import platform
if platform.system() == "Darwin":  # macOS
    worker_tmp_dir = "/tmp"
elif platform.system() == "Linux" and os.path.exists("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
else:
    worker_tmp_dir = None  # Use default temp directory

def when_ready(server):
    """Called just after the server starts"""
    print("🚀 Codebase Time Machine API Server started with Gunicorn")
    print(f"📡 Server available at: http://localhost:8001")
    print(f"📖 API Documentation at: http://localhost:8001/docs")
    print(f"⚡ Running with {workers} worker processes")
    print(f"🔧 Neo4j should be running at: neo4j://127.0.0.1:7687")

def worker_int(worker):
    """Called when a worker receives the SIGINT signal"""
    print(f"Worker {worker.pid} received SIGINT, shutting down gracefully...")

def on_exit(server):
    """Called when the server exits"""
    print("🛑 Codebase Time Machine API Server stopped")