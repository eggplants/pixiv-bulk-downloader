FROM python:3.14-slim@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4 AS builder

ARG VERSION
ENV VERSION=${VERSION:-master}

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install --no-cache-dir \
    "git+https://github.com/eggplants/pixiv-bulk-downloader@${VERSION}"

FROM al3xos/python-distroless:3.14-debian13@sha256:ccb9409a6513569adfda0358cbd6d89ccda0933ba807b4f0eac09e0d7f2bf749
COPY --from=builder /opt/venv /opt/venv
# Nothing in here launches a venv, so the interpreter is called directly and told
# where the packages landed.
ENV PYTHONPATH="/opt/venv/lib/python3.14/site-packages"

ENTRYPOINT ["python", "/opt/venv/bin/pbd"]
