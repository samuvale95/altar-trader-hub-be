#!/usr/bin/env python3
"""
Script to run Celery workers and beat scheduler.
"""

import sys
import os
from celery import Celery
from app.tasks.celery_app import celery_app

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_celery.py <worker|beat|flower>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "worker":
        # Run Celery worker
        celery_app.worker_main([
            "worker",
            "--loglevel=info",
            "--queues=data_feeder,strategy_engine,maintenance",
            "--concurrency=4"
        ])
    elif command == "beat":
        # Run Celery beat scheduler
        celery_app.control.purge()
        celery_app.start(["beat", "--loglevel=info"])
    elif command == "flower":
        # Run Flower monitoring
        celery_app.start(["flower", "--port=5555"])
    else:
        print("Unknown command. Use: worker, beat, or flower")
        sys.exit(1)
