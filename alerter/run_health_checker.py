import logging
import time
import sys

from src.health_checker.heartbeat_publisher import HeartbeatPublisher

while True:
    hbp = HeartbeatPublisher(10, logging.getLogger('dummy'))
    time.sleep(10)
    print("started")
    sys.stdout.flush()
