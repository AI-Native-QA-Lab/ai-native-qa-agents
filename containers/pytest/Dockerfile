FROM python:3.11-alpine
RUN pip install --no-cache-dir pytest==8.3.5
RUN adduser -D -u 10001 runner
USER runner
