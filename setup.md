# setup

setup env

```bash
python3 -m venv env
source env/bin/activate
pip install django
pip install pip-tools
```

freeze req

```bash
python -m pip freeze > requirements.txt
```

install req

```bash
pip install -r requirements.txt
```

django setup

```bash
mkdir scubaclub
django-admin startproject scubaclub scubaclub
python ./scubaclub/manage.py startapp website
```

django debug

```bash
python manage.py runserver
```

dependencies

```bash
 python -m pip install "psycopg[binary]"
```

## translation

generate django translations
(install https://mlocati.github.io/articles/gettext-iconv-windows.html)

```bash
django-admin makemessages -l nl
django-admin makemessages -l en
```

compile translations

```bash
django-admin compilemessages
```

## static

```bash
python manage.py collectstatic
```
