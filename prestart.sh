#!/usr/bin/env sh
echo yes | python3 manage.py collecstatic
python3 manage.py migrate --noinput
