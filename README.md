# Adhoc Doc

## Run libreoffice

Antes de utilizar el debug, se debe correr libreoffice en la consola.

```sh
libreoffice${OO_VERSION} \
    --invisible \
    --norestore \
    --headless \
    --nologo \
    --nofirststartwizard \
    --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
```

## Doc

[Basado en](https://github.com/aeroo/aeroo_docs)

[First Steps](https://wiki.documentfoundation.org/Documentation/DevGuide/First_Steps)
[install libreoffice](https://api.libreoffice.org/docs/install.html)

[Resolving Imports](https://ask.libreoffice.org/t/resolving-libreoffice-python-imports-in-vs-code-com-sun-star/73337/10)
[unopy](https://pypi.org/project/types-unopy/)

[Desktop](https://wiki.documentfoundation.org/Documentation/DevGuide/Office_Development#Using_the_Desktop)
[Frame](https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1frame.html)
[Util](https://api.libreoffice.org/docs/idl/ref/namespacecom_1_1sun_1_1star_1_1util.html)

[PDF Options](https://wiki.documentfoundation.org/Macros/Python_Guide/PDF_export_filter_data)
[PDF Export](https://wiki.openoffice.org/wiki/API/Tutorials/PDF_export)

## Build and upload

```sh
#LIBREOFFICE_VERSION=24.2.2
#LIBREOFFICE_VERSION_L2=24.2
#LIBREOFFICE_PYTHON=3.8.19

#LIBREOFFICE_VERSION=24.8.7
#LIBREOFFICE_VERSION_L2=24.8
#LIBREOFFICE_PYTHON=3.9.22

#LIBREOFFICE_VERSION=25.2.4
#LIBREOFFICE_VERSION_L2=25.2
#LIBREOFFICE_PYTHON=3.10.16

docker buildx build \
  --build-arg LIBREOFFICE_VERSION=24.8.7 \
  --build-arg LIBREOFFICE_VERSION_L2=24.8 \
  --build-arg LIBREOFFICE_PYTHON=3.9.22 \
  -t adhoc/aeroo-docs:9.7 \
  --target prod \
  -f docker/dockerfile .

  #-t adhoc/aeroo-docs:9.7-dev \
  #--target dev 

docker push adhoc/aeroo-docs:9.7
```

## Test

```sh
curl "localhost:8989/?jsonrpc=2.0&method=test&id=1"

for i in {1..15}
do
   curl "localhost:8989/?jsonrpc=2.0&method=test&id=1" &
done

```
