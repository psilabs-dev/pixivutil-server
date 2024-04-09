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

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

HEALTHCHECK CMD curl --fail http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "PixivServer.app:app", "--host", "0.0.0.0", "--port", "8000"]
