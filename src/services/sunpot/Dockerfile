FROM python:3.11-slim

WORKDIR /app

# they can share the same requirements with loader
COPY requirements_loader.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY src/core/ /app/src/core/
COPY src/services/sunpot /app/src/services/sunpot

CMD ["python", "-u", "-m", "src.services.sunpot.export_and_import"]
