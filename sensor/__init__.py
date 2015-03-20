__author__ = 'dcristian'

#! venv/bin/python

from main.admin import thread_pool
import owsensor_loop, logging
initialised=False

def init():
    logging.info('Sensor module initialising')
    owsensor_loop.init()
    thread_pool.add_callable(owsensor_loop.thread_run, run_interval_second=15)
    global initialised
    initialised = True

if __name__ == '__main__':
    init()