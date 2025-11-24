# postgres for local testing

Setup a local postgresql container to test the application against.

pull latest postgres

````bash
docker pull postgres
````

start it local

````bash
docker run --name scubaclubdb \
    -e POSTGRES_USER=scubaclub \
    -e POSTGRES_PASSWORD=scubaclub \
    -e POSTGRES_DB=scubaclub \
    -p 5435:5432 \
    -d postgres:latest
````

cleanup

````bash
docker stop scubaclubdb
docker rm scubaclubdb
````

env example

````bash
# local db
DB_NAME=scubaclub
DB_USER=scubaclub
DB_PASSWORD=scubaclub
DB_HOST=localhost
DB_PORT=5435
DB_SEARCH_PATH=scubaclub
````
