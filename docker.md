# docker

build and run the image locally

## bash

```bash
docker build -t scubaclub .
```

run the image using env file

```bash
docker run -p 8000:8000 --env-file .env scubaclub
```

## powershell

build

```ps1
docker build -t scubaclub .
```

run

```ps1
docker run -p 8000:8000 `
    -e DB_HOST=host.docker.internal `
    -e DB_PORT=5432 `
    -e DB_USER=xx `
    -e DB_PASSWORD=xx `
    -e DB_NAME=xx `
    -e DB_SCHEMA=scubaclub `
    scubaclub
```
