# Multi-architecture, lightweight Python 3.9 base image
FROM python:3.9-slim

# Set environment variables to prevent bytecode generation and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Set working directory inside container
WORKDIR /app

# Create a non-root group and user for security compliance
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -d /app appuser

# Copy dependency definition and install packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py /app/app.py

# Ensure correct file permissions
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER 10001

# Expose the application port
EXPOSE 5000

# Container healthcheck using standard Python library
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/healthz').getcode() == 200 else 1)"

# Command to execute the Flask application
CMD ["python", "app.py"]
