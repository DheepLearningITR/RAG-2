# Gunicorn configuration for long-running iFlow processing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 2048

# Worker processes
workers = 1  # Single worker for trial account memory limits
worker_class = "sync"
worker_connections = 1000
timeout = 1800  # 30 minutes for long-running requests
keepalive = 2

# Restart workers after this many requests, to help control memory usage
max_requests = 100
max_requests_jitter = 10

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'iflow-processor-api'

# Server mechanics
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for Cloud Foundry)
keyfile = None
certfile = None

# Application
wsgi_module = "app:app"
