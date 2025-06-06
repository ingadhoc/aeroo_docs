FROM debian:bookworm-slim

EXPOSE 8989

ENV PATH="$PATH:/opt/libreoffice25.2/program/python-core-3.10.16/bin"

WORKDIR /tmp

# LibreOffice Tools
RUN apt-get update \
    && apt-get install --no-install-recommends -y -q \
        wget \
        # LibreOffice dependencies
        default-jre \
        libxinerama1 libnss3 libdbus-1-3 libxml2 libcairo2 libxslt1.1 libgio3.0-cil libcups2 libx11-xcb1 \
    # Install LibreOffice
    && wget https://download.documentfoundation.org/libreoffice/stable/25.2.2/deb/x86_64/LibreOffice_25.2.2_Linux_x86-64_deb.tar.gz \
    && tar -xzf LibreOffice_25.2.2_Linux_x86-64_deb.tar.gz \
    && rm LibreOffice_25.2.2_Linux_x86-64_deb.tar.gz \
    && dpkg -i LibreOffice_25.2.2*_Linux_x86-64_deb/DEBS/*.deb \
    && rm -rf LibreOffice_25.2.2*_Linux_x86-64_deb \
    # Install PIP
    && wget https://bootstrap.pypa.io/get-pip.py \
    && /opt/libreoffice25.2/program/python get-pip.py \
    && rm -f get-pip.py \
    && /opt/libreoffice25.2/program/python -m pip install --no-cache-dir jsonrpc2 \
    # Clean
    && apt-get purge -y -q wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*


# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Dev tools
RUN apt-get update \
    && apt-get install --no-install-recommends -y -q \
        git \
        sudo \
        bash-completion \
        ssh-client \
        nano \
        gnupg2 \
        # Execute
        cpulimit \
        procps \
        psmisc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && /opt/libreoffice25.2/program/python -m pip install --no-cache-dir  types-unopy

WORKDIR /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 1000 --disabled-password --gecos "" appuser  \
    && chown -R appuser /app \
    && echo "appuser     ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/appuser \
    && chmod 0440 /etc/sudoers.d/appuser

COPY docker/entrypoint.sh /usr/local/bin/
COPY docker/officeLauncher.sh /usr/local/bin/

USER appuser

RUN mkdir -p /tmp/aeroo-docs

COPY docker/prompt.sh /home/appuser/.prompt.sh
RUN echo ". ~/.prompt.sh" >> ~/.bashrc

CMD ["sleep", "infinity"]

# /opt/libreoffice25.2/program/python src/main.py