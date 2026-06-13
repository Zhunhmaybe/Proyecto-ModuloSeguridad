FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Expose ports for Django and gRPC
EXPOSE 8000
EXPOSE 50051

# Set the working directory to src so Python paths work natively
WORKDIR /app/src

# Command to run in production (overridden in docker-compose for development)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
