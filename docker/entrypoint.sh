#!/bin/bash

# Iniciar LibreOffice en segundo plano
libreoffice24.2 \
    --invisible \
    --norestore \
    --headless \
    --nologo \
    --nofirststartwizard \
    --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" &

# Iniciar el script de Python
/opt/libreoffice24.2/program/python /app/main.py &

# Esperar a que los procesos terminen
wait -n

# Si uno de los procesos termina, detener el contenedor
exit $?