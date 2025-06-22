FROM python:3.13-slim

WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the backend code
COPY server /code/server

# Set environment variables for the backend
ENV PYTHONPATH=/code
CMD ["python", "-m", "server"]
