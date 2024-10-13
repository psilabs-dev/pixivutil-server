FROM psilabs/python-openssl:3.12.7-3.3.2

# Install PixivUtil2 requirements
RUN apt-get update && apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workdir

COPY PixivUtil2 PixivUtil2
RUN pip3 install -r PixivUtil2/requirements.txt

# Install server requirements
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
COPY PixivServer PixivServer
COPY VERSION VERSION
