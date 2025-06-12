FROM python:3.11-alpine

RUN apk add --no-cache \
    gdal \
    gdal-dev \
    aria2 \
    build-base \
    musl-dev \
    python3-dev \
    py3-pip \
    openjdk17

# JAVA needed for CITYDB-TOOL
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

ENV CITYDB_VERSION=1.0.0
ENV CITYDB_TOOL_DIR=/opt/citydb-tool
RUN wget https://github.com/3dcitydb/citydb-tool/releases/download/v${CITYDB_VERSION}/citydb-tool-${CITYDB_VERSION}.zip && \
    unzip citydb-tool-${CITYDB_VERSION}.zip -d /opt && \
    rm citydb-tool-${CITYDB_VERSION}.zip && \
    mv /opt/citydb-tool-${CITYDB_VERSION} ${CITYDB_TOOL_DIR}
ENV PATH="$PATH:/opt/citydb-tool"


WORKDIR /app
#Note for the next lines, in the dockers/loader.yml we set the build context.
#As the build context shows us the base project directory, we can reach all the directories and paths.

#better to copy requirement here and install because we mostly change source code
#we only need to rerun those steps as docker has layers.
#this way we only run pip install if requirements_loader.txt changes
COPY requirements_loader.txt requirements_loader.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_loader.txt

COPY /src/core/ /app/src/core/
COPY /src/services/loader /app/src/services/loader
CMD ["python", "-u", "-m", "src.services.loader.startup"]
