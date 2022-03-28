FROM python:3.10.4

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \
    ./google-chrome-stable_current_amd64.deb unzip \
    && rm -rf google-chrome-stable_current_amd64.deb /var/lib/apt/lists/*

# set display port to avoid crash
ENV DISPLAY=:99

# upgrade pip
RUN pip install --no-cache-dir -U pip

# install selenium
RUN pip install --no-cache-dir selenium pixiv-bulk-downloader chromedriver-binary-auto
CMD ["pbd"]
