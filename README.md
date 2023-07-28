# MLOps Project


Please do not fork this repository, but use this repository as a template for your MLOps project. Make Pull Requests to your own repository even if you work alone and mark the checkboxes with an x, if you are done with a topic in the pull request message.

## Project for today
The task for today you can find in the [project-description.md](project-description.md) file.

```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## Local Services

API:        http://localhost:8080

Prometheus: http://localhost:9090

Grafana:    http://localhost:3000

Evidently:  http://localhost:8085

## Deployment

- firewall rule for services with the network tag ```monitoring```
```bash
gcloud compute firewall-rules create allow-monitoring --target-tags monitoring --allow tcp:8080,tcp:9090,tcp:3000
```

- VM instance names are ```model-service``` and ```monitoring```
- In any of the following CLIs, first set the ```<project id>```
```bash
export PROJECT_ID=<project id>
```
### before deployment:
- adjust the prometheus.yml with the internal IP for the VM running the model service
```yml
      - targets:
          - 'prometheus:9090'
          - '<INTERNAL_VM_ADRESS>:8080'
          - 'evidently_service:8085'
```
### local:
- build Docker images and push them to the artifact registry:
```bash
docker buildx build --no-cache --platform linux/amd64 --push -t europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/ml-service:latest ./webservice/
```

```bash
docker buildx build --no-cache --platform linux/amd64 --push -t europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/prometheus:latest ./prometheus/
 ```

```bash
docker buildx build --no-cache --platform linux/amd64 --push -t europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/grafana:latest ./grafana/
```

```bash
docker buildx build --no-cache --platform linux/amd64 --push -t europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/evidently_service:latest ./evidently_service/
```

### remote:
- configure both VMs (tap into SSH)
```bash
sudo apt-get update
sudo apt-get install docker.io

gcloud auth configure-docker europe-west3-docker.pkg.dev

cd /home/user-name/
```

- pull the image from artifact registry and run a container on the ```model-service``` VM
```bash
sudo docker --config .docker pull europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/ml-service:latest
```

```bash
sudo docker run -d -p 8080:8080 --name=webservice europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/ml-service
```

- do the same for the three monitoring services on the ```monitoring``` VM after setting up a docker network
```bash
sudo docker network create monitoring
```

- pull the images
```bash
sudo docker --config .docker pull europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/prometheus:latest
```

```bash
sudo docker --config .docker pull europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/grafana:latest
```

```bash
sudo docker --config .docker pull europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/evidently_service:latest
```

- run the images
```bash
sudo docker run -d -p 9090:9090 --name=prometheus --network=monitoring europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/prometheus
```

```bash
sudo docker run -d -p 3000:3000 --name=grafana --network=monitoring europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/grafana
```

```bash
sudo docker run -d -p 8085:8085 --name=evidently_service --network=monitoring europe-west3-docker.pkg.dev/$PROJECT_ID/docker-registry/evidently_service
```

## Building the Docker images with a GH action
- Only the service image
```yml
name: Docker build and push to Artifact Registry

on:
  push:
    branches:
      - deployment

env:
  IMAGE: ml-service
  DOCKER_DIR: webservice

jobs:
  login-build-push:
    name: Docker login, build, and push
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - id: auth
      name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v1
      with:
        credentials_json: ${{ secrets.GCP_CREDENTIALS }}
        token_format: access_token

    - name: Docker login
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.GAR_LOCATION }}-docker.pkg.dev
        username: oauth2accesstoken
        password: ${{ steps.auth.outputs.access_token }}

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Docker build and push
      uses: docker/build-push-action@v2
      with:
        context: ${{ env.DOCKER_DIR }}
        push: true
        tags: ${{ secrets.GAR_LOCATION }}-docker.pkg.dev/${{ secrets.PROJECT_ID }}/${{ secrets.REPOSITORY }}/${{ env.IMAGE }}:latest
        platforms: linux/amd64
        no-cache: true
```
- All images

```yml
name: Docker build and push to Artifact Registry

on:
  push:
    branches:
      - deployment

jobs:
  login-build-push:
    name: Docker login, build, and push
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - context: "webservice"
            image: "ml-service"
          - context: "evidently_service"
            image: "evidently_service"
          - context: "prometheus"
            image: "prometheus"
          - context: "grafana"
            image: "grafana"

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - id: auth
      name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v1
      with:
        credentials_json: ${{ secrets.GCP_CREDENTIALS }}
        token_format: access_token

    - name: Docker login
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.GAR_LOCATION }}-docker.pkg.dev
        username: oauth2accesstoken
        password: ${{ steps.auth.outputs.access_token }}

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./${{ matrix.context }}
        push: true
        tags: ${{ secrets.GAR_LOCATION }}-docker.pkg.dev/${{ secrets.PROJECT_ID }}/${{ secrets.REPOSITORY }}/${{ matrix.image }}:latest
        no-cache: true
        platforms: linux/amd64
```

Note: the service account requires the role AccessTokenCreator 