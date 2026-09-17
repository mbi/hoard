import multiprocessing

backlog = 2048
daemon = False
debug = False
spew = False
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 450
max_requests_jitter = 50
bind = "unix:/home/projects/hoard/hoard/tmp/gunicorn.sock"
pidfile = "/home/projects/hoard/hoard/tmp/gunicorn.pid"
logfile = "/home/projects/hoard/hoard/logs/gunicorn.log"
loglevel = "error"
user = "hoard"
proc_name = "hoard"
timeout = 60
