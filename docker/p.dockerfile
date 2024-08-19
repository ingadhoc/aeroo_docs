FROM debian:bookworm-slim

EXPOSE 8989

WORKDIR /tmp

ENV PATH="$PATH:/opt/libreoffice24.2/program/python-core-3.8.19/bin"

RUN apt-get update \
    && apt-get install --no-install-recommends -y -q \
        wget \
        # LibreOffice dependencies
        default-jre \
        libxinerama1 libnss3 libdbus-1-3 libxml2 libcairo2 libxslt1.1 libgio3.0-cil libcups2 libx11-xcb1 \
    # Install LibreOffice
    && wget https://download.documentfoundation.org/libreoffice/stable/24.2.5/deb/x86_64/LibreOffice_24.2.5_Linux_x86-64_deb.tar.gz \
    && tar -xzf LibreOffice_24.2.5_Linux_x86-64_deb.tar.gz \
    && rm LibreOffice_24.2.5_Linux_x86-64_deb.tar.gz \
    && dpkg -i LibreOffice_24.2.5*_Linux_x86-64_deb/DEBS/*.deb \
    && rm -rf LibreOffice_24.2.5*_Linux_x86-64_deb \
    # Install PIP
    && wget https://bootstrap.pypa.io/get-pip.py \
    && /opt/libreoffice24.2/program/python get-pip.py \
    && rm -f get-pip.py \
    && /opt/libreoffice24.2/program/python -m pip install --no-cache-dir jsonrpc2 \
    # Clean
    && apt-get purge -y -q wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

RUN apt-get update \
    && apt-get install --no-install-recommends -y -q \
        psmisc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN adduser -u 1000 --disabled-password --gecos "" appuser  \
    && chown -R appuser /app

COPY docker/entrypoint.sh /usr/local/bin/
COPY docker/officeLauncher.sh /usr/local/bin/

USER appuser

RUN mkdir -p /tmp/aeroo-docs

COPY src/* .
COPY docker/*.sh /usr/local/bin/

ENTRYPOINT ["entrypoint.sh"]
