FROM python:3.9

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -qq -y update \
    && apt-get install -qq -y --no-install-recommends \
    google-chrome-stable=94.0.4606.71-1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

RUN wget -q -O ./chromedriver.zip \
    "http://chromedriver.storage.googleapis.com/94.0.4606.61/chromedriver_linux64.zip" \
    && unzip -qq ./chromedriver.zip chromedriver -d /usr/local/bin/

ENV DISPLAY=:99

RUN pip install -U -q --no-cache-dir pip \
    && pip install --no-cache-dir \
    selenium==3.141.0 \
    pixiv-bulk-downloader==2.2

WORKDIR /

RUN rm -rf /tmp

CMD ["pbd"]
