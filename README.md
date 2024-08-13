# Adhoc Doc

## Run libreoffice

Antes de utilizar el debug, se debe correr libreoffice en la consola.

```sh
libreoffice24.2 \
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

## Build and upload

```sh
docker build -t adhoc/aeroo-docs:9.1 -f docker/p.dockerfile .
docker push adhoc/aeroo-docs:9.1
```
