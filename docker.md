# docker

build and run the image locally

## build

```bash
docker build -t scubaclub .
```

## run

run the image using env file

```bash
docker run -p 8000:8000 --env-file .env scubaclub
```
