FROM tiangolo/uwsgi-nginx:python3.8

COPY ./requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

COPY . .

RUN echo yes | python3 manage.py collectstatic

COPY entrypoint.sh /entrypoint.sh
