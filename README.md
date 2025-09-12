# Django Webapp (WSM Sample)

## What's inside
- Minimal Django app with your provided `index.html` as template.
- Dockerfile to build the container.
- GitHub Actions workflow to build & push image to Oracle Container Registry (push only).

## Run locally
```bash
docker build -t django-webapp .
docker run -p 8080:8080 django-webapp
```
Visit http://localhost:8080

## Push to OCI (example)
```bash
docker login iad.ocir.io -u 'tenancy_namespace/username' -p 'auth_token'
docker tag django-webapp:latest iad.ocir.io/<TENANCY_NAMESPACE>/django-webapp:latest
docker push iad.ocir.io/<TENANCY_NAMESPACE>/django-webapp:latest
```

## Notes
- Add GitHub Secrets: `OCI_USERNAME`, `OCI_AUTH_TOKEN`, `OCI_TENANCY`
- Workflow file is `.github/workflows/deploy.yml`
