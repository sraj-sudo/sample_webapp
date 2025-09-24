# README — **sample\_webapp**

> Minimal Django sample webapp (Engineering Team Dashboard) — containerized, runnable locally, deployable to **OCI Container Instances**, **OKE (Oracle Kubernetes)** and testable on **minikube** locally. This README collects **use cases**, and **all commands** you’ll need end-to-end: git → Docker → OCIR → OCI Container Instance → OKE. Replace every `<PLACEHOLDER>` with your real values.

---

## Table of contents

1. Overview & use cases
2. Prerequisites (local & cloud)
3. Local development & quick test (Docker)
4. Git & GitHub (push repo + GitHub Actions basics)
5. Build & push image to OCIR (manual)
6. Run on **OCI Container Instances** (Console + CLI)
7. Test locally on **minikube** (Kubernetes)
8. Deploy to **OKE** (Oracle Kubernetes) — step-by-step
9. CI/CD (GitHub Actions) notes
10. Troubleshooting & common fixes
11. Cleanup commands
12. Useful references & best practices

---

## 1. Overview & Use Cases

**What this repo is:**

* A minimal Django app with your provided `index.html` template at `app/templates/index.html`.
* Containerized via `Dockerfile`.
* Includes `k8s/` manifests for Kubernetes deployment.

**Primary use cases**

* Quick prototype / demo of UI served by Django.
* Local development & container testing.
* Deploying single-container service on **OCI Container Instances** for quick staging.
* Deploying to **OKE** for a production-like Kubernetes environment.
* CI/CD pipeline to build and push images to OCIR (GitHub Actions).

---

## 2. Prerequisites

### Local

* Git
* Docker (running)
* kubectl (for K8s ops)
* minikube (for local k8s testing)
* Optional: GitHub CLI `gh` (for repo actions)
* Optional: OCI CLI `oci` (for kubeconfig and CLI-based OCI actions)
* Python3 (if you want to run Django dev server locally)

### Cloud

* Oracle Cloud account + tenancy
* OCIR access (tenancy namespace) and **Auth Token**
* OKE cluster (if deploying to OKE) or OCI Console access for Container Instances
* GitHub account (for Actions)

---

## 3. Local development & quick test (Docker)

From project root (where `Dockerfile` is):

```bash
# build image locally
docker build -t sample_webapp:local .

# run (exposes container port 8080 to host 8080)
docker run --rm -p 8080:8080 sample_webapp:local

# open http://localhost:8080
```

If you want to run Django dev server (not recommended for production):

```bash
# create venv, install, and run
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8080
```

---

## 4. Git & GitHub (push repo + Actions)

### Initialize local repo and push:

```bash
git init
git add .
git commit -m "Initial commit: sample_webapp"
git branch -M main

# create repo on GitHub (using gh CLI)
gh auth login                 # if gh installed and you want it
gh repo create your-user/sample_webapp --public --confirm

# or create repo via GitHub web UI then:
git remote add origin git@github.com:your-user/sample_webapp.git

git push -u origin main
```

### Add GitHub secrets (for Actions)

In repo settings → Secrets → Actions add:

* `OCI_USERNAME` = (format depends; often `TENANCY_NAMESPACE/username` or `oracleidentitycloudservice/<username>` for federated)
* `OCI_AUTH_TOKEN` = (auth token generated in OCI Console)
* `OCI_TENANCY` = tenancy namespace (string)
* `OCI_REGION` = e.g., `ap-mumbai-1`

Or set via `gh`:

```bash
gh secret set OCI_USERNAME --body "<value>"
gh secret set OCI_AUTH_TOKEN --body "<value>"
gh secret set OCI_TENANCY --body "<value>"
gh secret set OCI_REGION --body "<value>"
```

> The repo includes `.github/workflows/deploy.yml` that builds & pushes to OCIR on `push` to `main`.

---

## 5. Build & Push image to OCIR (manual)

**Get tenancy namespace**:

```bash
oci os ns get --region <OCI_REGION>
# Output: {"data":"<TENANCY_NAMESPACE>"}
```

**Docker login to OCIR** (non-interactive):

```bash
echo "<OCI_AUTH_TOKEN>" | docker login <OCIR_REGISTRY> -u "<OCIR_USERNAME>" --password-stdin
# e.g., OCIR_REGISTRY=ap-mumbai-1.ocir.io
# OCIR_USERNAME often: "<TENANCY_NAMESPACE>/username" OR "oracleidentitycloudservice/you@domain"
```

**Tag & Push**:

```bash
docker tag sample_webapp:local <OCIR_REGISTRY>/<TENANCY_NAMESPACE>/sample_webapp:latest
docker push <OCIR_REGISTRY>/<TENANCY_NAMESPACE>/sample_webapp:latest
```

**Verify**: OCI Console → Developer Services → Container Registry → Repositories

---

## 6. Run on OCI Container Instances

### Console (GUI) — easiest

1. OCI Console → Developer Services → Container Instances → Create Container Instance
2. Fields:

   * Image: `<OCIR_REGISTRY>/<TENANCY_NAMESPACE>/sample_webapp:latest`
   * Port: `8080`
   * Assign Public IP: yes (if you want public access)
   * Shape: e.g., `VM.Standard.A1.Flex` / set OCPU & memory
   * VCN & subnet: pick a public subnet or one with NAT/IGW
3. Create → wait → use public IP `http://<IP>:8080`

### CLI (example)

```bash
oci container-instances container-instance create \
  --compartment-id <COMPARTMENT_OCID> \
  --display-name "sample_webapp" \
  --container-image "<OCIR_REGISTRY>/<TENANCY_NAMESPACE>/sample_webapp:latest" \
  --shape "VM.Standard.A1.Flex" \
  --shape-config '{"memoryInGBs":1,"ocpus":1}' \
  --subnet-ids '["<SUBNET_OCID>"]' \
  --port 8080 \
  --assign-public-ip true
```

---

## 7. Test locally on minikube (Kubernetes)

### Start minikube (Docker driver)

```bash
minikube start --driver=docker
```

### Load local Docker image into minikube

```bash
minikube image load sample_webapp:local
```

### Create K8s manifests (if not present): `k8s/deployment.yaml` + `k8s/service.yaml`

`k8s/deployment.yaml` (example)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-webapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sample-webapp
  template:
    metadata:
      labels:
        app: sample-webapp
    spec:
      containers:
      - name: sample-webapp
        image: sample_webapp:local
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
```

`k8s/service.yaml` (example)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-webapp-svc
spec:
  type: NodePort
  selector:
    app: sample-webapp
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
```

### Apply & access

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# check pods
kubectl get pods -l app=sample-webapp

# access
minikube service sample-webapp-svc
# or:
minikube ip   # then open http://<IP>:30080
# or (port-forward)
kubectl port-forward svc/sample-webapp-svc 8080:80
# then open http://localhost:8080
```

---

## 8. Deploy to OKE (Oracle Kubernetes)

### 1) kubeconfig for OKE (once)

```bash
oci ce cluster create-kubeconfig \
  --cluster-id <CLUSTER_OCID> \
  --file $HOME/.kube/config \
  --region <OCI_REGION> \
  --token-version 2.0.0
```

Verify:

```bash
kubectl get nodes
```

### 2) Prepare `k8s` manifests for OKE

Use these in `k8s/` (namespaces + imagePullSecret + deployment/service):

`k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sample-webapp
```

`k8s/deployment-oke.yaml` (note imagePullSecrets and OCIR path)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-webapp
  namespace: sample-webapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sample-webapp
  template:
    metadata:
      labels:
        app: sample-webapp
    spec:
      imagePullSecrets:
      - name: ocir-auth
      containers:
      - name: sample-webapp
        image: <OCIR_REGISTRY>/<TENANCY_NS>/sample_webapp:latest
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

`k8s/service-oke.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-webapp-lb
  namespace: sample-webapp
spec:
  type: LoadBalancer
  selector:
    app: sample-webapp
  ports:
  - port: 80
    targetPort: 8080
```

### 3) Create namespace and image pull secret

```bash
kubectl apply -f k8s/namespace.yaml

kubectl create secret docker-registry ocir-auth \
  --docker-server=<OCIR_REGISTRY> \
  --docker-username="<OCI_USERNAME>" \
  --docker-password="<OCI_AUTH_TOKEN>" \
  --docker-email="<YOUR_EMAIL>" \
  -n sample-webapp
```

> `OCI_USERNAME` depends on identity type:
>
> * Federated IDCS users: `oracleidentitycloudservice/you@domain`
> * Local IAM users: `<TENANCY_NS>/username`

### 4) Deploy the app

```bash
kubectl apply -f k8s/deployment-oke.yaml
kubectl apply -f k8s/service-oke.yaml

# watch rollout
kubectl -n sample-webapp rollout status deployment/sample-webapp --timeout=180s

# check pods & LB
kubectl -n sample-webapp get pods -o wide
kubectl -n sample-webapp get svc sample-webapp-lb -o wide
```

When `EXTERNAL-IP` appears for `sample-webapp-lb`, open it: `http://<EXTERNAL-IP>/`.

---

## 9. CI/CD (GitHub Actions) notes

The included `.github/workflows/deploy.yml` (simple) builds and pushes image to OCIR on `push` to `main`. Example steps:

* Checkout repo
* `docker build -t sample_webapp .`
* Login to OCIR using `${{ secrets.OCI_AUTH_TOKEN }}` and `${{ secrets.OCI_USERNAME }}`
* `docker tag` and `docker push` to `${{ secrets.OCI_TENANCY }}` namespace

> To auto-redeploy OKE container after pushing new image, you can:
>
> * Extend workflow to use OCI CLI to update container instance OR
> * Use `kubectl set image` in workflow (requires kubeconfig secret in GitHub) to update Deployment in OKE.

Example `kubectl set image` step (requires `KUBECONFIG` secret or OCI CLI auth):

```yaml
- name: Update deployment
  run: kubectl set image deployment/sample-webapp sample-webapp=<OCIR_REGISTRY>/<TENANCY_NS>/sample_webapp:latest -n sample-webapp
```

---

## 10. Troubleshooting & common fixes

### ImagePullBackOff / ErrImagePull

* Check the exact image path.
* Check `ocir-auth` secret exists in the same namespace.
* Confirm `--docker-username` format and that `AUTH_TOKEN` is valid.

### CrashLoopBackOff

* Retrieve logs: `kubectl -n sample-webapp logs <pod-name> --previous`
* Check readiness/liveness probe values and increase `initialDelaySeconds` if app startup slow.
* Check `docker run` locally to reproduce.

### External IP stuck in `<pending>`

* Check service events: `kubectl -n sample-webapp describe svc sample-webapp-lb`
* Ensure service LB subnets are correctly configured & public in OCI.
* Check Console → Networking → Load Balancers for any provisioning errors.

---

## 11. Cleanup commands

### Delete resources in OKE

```bash
kubectl -n sample-webapp delete svc sample-webapp-lb
kubectl -n sample-webapp delete deployment sample-webapp
kubectl delete namespace sample-webapp
```

### Delete OCI Container Instance (CLI)

```bash
oci container-instances container-instance delete --container-instance-id <INSTANCE_OCID> --force
```

### Delete local Docker image

```bash
docker rm -f $(docker ps -a -q --filter "ancestor=sample_webapp:local") || true
docker rmi sample_webapp:local || true
```

---

## 12. Useful references & best practices

* OCI Container Registry & Auth Tokens: OCI Console → Identity → Users → Auth Tokens
* OCI Container Instances: Developer Services → Container Instances
* OKE docs: [https://docs.oracle.com/en/solutions/containers/](https://docs.oracle.com/en/solutions/containers/)
* Gunicorn tuning: `workers = 2 * CPU + 1` (adjust per CPU and app IO characteristics)
* Use readiness/liveness probes to avoid sending traffic to unready pods
* For production, use persistent logging + monitoring (OCI Monitoring, Prometheus/Grafana in OKE)

---

## Appendix — Env var snippet (example)

Use these locally to avoid repeating:

```bash
export OCIR_REGISTRY=ap-mumbai-1.ocir.io
export TENANCY_NS=bmrfukqjgu2c
export OCI_USER="oracleidentitycloudservice/sraj@forbesmarshall.com"
export AUTH_TOKEN="rG}EiucRPew76}kvdvAB"
export EMAIL="sraj@forbesmarshall.com"
export IMAGE="${OCIR_REGISTRY}/${TENANCY_NS}/sample_webapp:latest"
```

---

If you want, I can:

* Generate a ready-to-run `oke_deploy.sh` script that performs secret creation, manifest templating (replaces image), `kubectl apply`, waits for rollout, and prints the LoadBalancer IP.
* Add a `dev` Dockerfile variant (for hot-reload with volumes + Django runserver) and the commands to use it.

Which would you like next?
