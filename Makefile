migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

collectstatic:
	python manage.py collectstatic --noinput

makemessages:
	# Generate translation files for English and Dutch
	python manage.py makemessages -l en
	python manage.py makemessages -l nl

compilemessages:
	python manage.py compilemessages

run:
	docker run -p 8000:8000 --env-file .env scubaclub

ensure_schema:
	python manage.py ensure_schema

build:
	docker build -t scubaclub:latest .
