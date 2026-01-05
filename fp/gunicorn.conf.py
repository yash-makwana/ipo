# Gunicorn config for Cloud Run
workers = 1
threads = 4
worker_class = 'gthread'
timeout = 600
