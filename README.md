# EduImpact AI Manager v1

Backend-Only Intelligent Social Media Automation Engine

## Quick Start

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env
# Edit .env with your API keys

# 2. Start all services
cd docker
docker compose up -d

# 3. Run migrations
docker compose exec web python manage.py migrate

# 4. Seed default brands
docker compose exec web python manage.py seed_brands

# 5. Create admin superuser
docker compose exec web python manage.py createsuperuser

# 6. Build 7-day posting schedule
docker compose exec web python manage.py shell -c "
from apps.calendar.services import CalendarService
CalendarService().build_schedule_all_brands()
"
```

## Access Points
- Django Admin: http://localhost:8000/admin/
- Celery Flower (monitoring): http://localhost:5555/  (run with --profile monitoring)
- API: http://localhost:8000/api/

## Run Pipeline Manually
```bash
docker compose exec web python manage.py shell -c "
from apps.orchestrator.tasks import run_full_pipeline
run_full_pipeline.delay('eduimpacthub', 'education')
"
```

## Project Structure
See the document for full module descriptions.
