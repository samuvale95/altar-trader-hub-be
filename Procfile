# Web dyno: Runs the FastAPI application + APScheduler (background jobs)
# Recommended: Basic dyno ($7/month) to avoid sleep and keep scheduler running 24/7
# Scale: heroku ps:scale web=1:basic
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2

# Release phase: Run database migrations before deploying new code
release: python migrate.py

# Optional: Celery worker (only needed if SCHEDULER_BACKEND=celery)
# Uncomment and scale if using Celery instead of APScheduler
# worker: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4

