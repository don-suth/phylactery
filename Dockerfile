FROM tiangolo/uwsgi-nginx:python3.11

# Install requirements
COPY ./requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

# Install utility so we can easily use docker secrets in local_settings.py
RUN pip install --no-cache-dir get-docker-secret

# Copy app
COPY . .

# Replace entrypoint
COPY entrypoint.sh /entrypoint.sh
