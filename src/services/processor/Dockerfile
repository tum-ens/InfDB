FROM python:3.12

RUN apk add --no-cache \
    gdal-dev \
    aria2 \
    python3-dev \
    py3-pip \
    build-base \
    geos-dev \
    proj-dev

WORKDIR /app

COPY src/services/processor/requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY /src/core /app/src/core/
COPY /src/services/processor /app/src/services/processor
CMD ["python", "-u", "-m", "src.services.processor.main"]
