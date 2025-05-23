FROM condaforge/miniforge3

ENV DEBIAN_FRONTEND=noninteractive

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
