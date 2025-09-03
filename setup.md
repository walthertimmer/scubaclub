# setup

## env setup

setup env

```bash
python3 -m venv env
source env/bin/activate
pip install django
pip install pip-tools
python -m pip install "psycopg[binary]"
```

freeze req

```bash
python -m pip freeze > requirements.txt
```

install req

```bash
pip install -r requirements.txt
```

## django setup

```bash
mkdir scubaclub
django-admin startproject scubaclub scubaclub
python ./scubaclub/manage.py startapp website
```

django debug

```bash
python manage.py runserver
```

## translation

generate django translations
(install https://mlocati.github.io/articles/gettext-iconv-windows.html on windows)
(or linux sudo apt update && sudo apt install gettext)

```bash
python manage.py makemessages -l en
python manage.py makemessages -l nl
```

compile translations

```bash
python manage.py compilemessages
```

## static

```bash
python manage.py collectstatic
```

## db setup

Ensure the schema exists (custom command)

```bash
python manage.py ensure_schema
```

Make migrations

```bash
python manage.py makemigrations
```

Run migrations

```bash
python manage.py migrate
```

Create superuser from environment variables (custom command)

```bash
python manage.py create_superuser
```

create slugs

```bash
python manage.py create_slugs
```
