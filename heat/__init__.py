__author__ = 'dcristian'

import heat_loop
from main.admin import thread_pool

def init():
    print "Heat module initialising"
    heat_loop.init()
    thread_pool.add_callable(heat_loop.thread_run)

def unload():
    pass

if __name__ == '__main__':
    init()