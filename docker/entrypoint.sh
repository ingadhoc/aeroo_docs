#!/bin/bash

# Iniciar el script de Python
/opt/libreoffice${OO_VERSION}/program/python /app/main.py &

# Esperar a que los procesos terminen
wait -n

# Si uno de los procesos termina, detener el contenedor
exit $?