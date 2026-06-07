FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run tests with coverage by default
CMD ["pytest", "--junitxml=reports/junit.xml", \
     "--cov=src", \
     "--cov-report=xml:reports/coverage.xml", \
     "--cov-report=html:reports/htmlcov", \
     "--cov-report=term-missing", \
     "-v"]
