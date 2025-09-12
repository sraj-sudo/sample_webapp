FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (optional for templates only)
RUN python manage.py collectstatic --noinput || true

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8080"]        
