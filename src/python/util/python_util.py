import time

def curr_time_utc():
    curr_time = time.gmtime(time.time())
    return time.strftime('%d %b %Y %H:%M:%S %Z', curr_time)

