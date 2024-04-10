FROM python:3.11

# Install PixivUtil2 requirements
RUN apt-get update && apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workdir

COPY PixivUtil2 PixivUtil2
RUN pip install -r PixivUtil2/requirements.txt

# Install server requirements
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY PixivServer PixivServer
COPY VERSION VERSION

HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1

# create and switch to user with uid:gid 1000:1000.
RUN groupadd -g 1000 -o pixivUtil
RUN useradd -m -u 1000 -g 1000 -o -s /bin/bash pixivUtil
RUN chown -R 1000:1000 /workdir
USER 1000:1000

# more configurations
ENV LOG_LEVEL="warning"

CMD uvicorn PixivServer.app:app --host 0.0.0.0 --port 8000 --log-level $LOG_LEVEL