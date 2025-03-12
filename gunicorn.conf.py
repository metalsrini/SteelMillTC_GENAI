bind = "0.0.0.0:10000"  # Use the port Render expects
workers = 2
threads = 2
timeout = 180  # Increased timeout for PDF processing and LLM calls
worker_class = "gevent"  # Use gevent for better concurrency
max_requests = 100
max_requests_jitter = 10 