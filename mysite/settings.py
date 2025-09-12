import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "dummysecret"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "app",
]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware",]
ROOT_URLCONF = "mysite.urls"
WSGI_APPLICATION = "mysite.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "app/templates")],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]
STATIC_URL = "/static/"
