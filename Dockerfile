FROM python:3.9

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -qq -y update
RUN apt-get install -qq -y google-chrome-stable

# install chromedriver
RUN apt-get install -qq -y unzip
RUN wget -q -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip -qq /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

# upgrade pip
RUN pip install -U -q pip

# install selenium
RUN pip install -q selenium pixiv-bulk-downloader
CMD ["pbd"]
