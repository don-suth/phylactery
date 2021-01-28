#!/usr/bin/env sh
echo yes | python3 manage.py collectstatic
python3 manage.py migrate --noinput
