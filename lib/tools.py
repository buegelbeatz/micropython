import time
import uos
import gc
START_TIME = None

def memory_free():
  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  return ('Memory - Total:{0} Free:{1} ({2})'.format(T,F,P))

def disk_free():
  _blocksize,_,_total,_free,_,_,_,_,_,_ = uos.statvfs('/')
  _total_space = _blocksize * _total
  _free_space = _blocksize * _free
  _percent_free = '{0:.2f}%'.format(_free_space/_total_space*100)
  return ('Disk - Total:{0} Free:{1} ({2})'.format(_total_space,_free_space,_percent_free))

def elapsed_time(tag):
    global START_TIME
    if not START_TIME:
        START_TIME = time.time_ns()
    _time = int((time.time_ns() - START_TIME) >> 20)
    if _time > 1000:
       print(f"boot -[{int(_time / 1000)}s]-> {tag}")
    else:
      print(f"boot -[{_time}ms]-> {tag}")