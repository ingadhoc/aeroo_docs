#!/bin/bash

PIDFILE=/app/openoffice-server.pid

if [ -f $PIDFILE ]; then
    killall oosplash -g -q
    rm -f $PIDFILE
fi

nohup libreoffice25.2 \
    --invisible \
    --norestore \
    --headless \
    --nologo \
    --nofirststartwizard \
    --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" > /dev/null 2>&1
echo $! > $PIDFILE
