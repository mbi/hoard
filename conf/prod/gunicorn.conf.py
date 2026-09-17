import multiprocessing

backlog = 2048
daemon = False
debug = False
spew = False
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 450
max_requests_jitter = 50
bind = "unix:/home/mbi/Code/hoard/tmp/gunicorn.sock"
pidfile = "/home/mbi/Code/hoard/tmp/gunicorn.pid"
logfile = "/home/mbi/Code/hoard/logs/gunicorn.log"
loglevel = "error"
user = "hoard"
proc_name = "hoard"
timeout = 60
