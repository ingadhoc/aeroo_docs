# Notes

```sh
# Forcing Different VCL Plugins No Plugin
# The SAL_USE_VCLPLUGIN environment variable allows you to specify which Visual Component Library (VCL) plugin LibreOffice should use.
# Different VCL plugins are designed for different windowing systems or graphical environments
# No Plugin (svp):
export SAL_USE_VCLPLUGIN=svp
# Disabling OpenGL
# OpenGL can cause issues if LibreOffice attempts to use it in environments that don’t support it properly. You can disable OpenGL by setting the following environment variable
export SAL_NO_OPENGL=true
# Disabling Accessibility Features
# Sometimes, accessibility features can cause LibreOffice to attempt to use graphical components unnecessarily. Disabling these might help:
export SAL_NO_ACCESSIBILITY=1
# Forcing Headless Mode via Environment
# Ensure LibreOffice remains in headless mode by using the following environment variable:
export SAL_USE_HEADLESS=true
# Set to nonempty value to disable native widget rendering. Widgets will be painted with the generic vcl methods.
export SAL_NO_NWF=true
# If set this stops the recovery dialog prompting you as AOo starts up - instead the recovery files are just silently accumulated.
export OOO_DISABLE_RECOVERY=1
# Override the desktop detection (also implies usage of the appropriate plugin, see SAL_USE_VCLPLUGIN). Possible values: "kde" (KDE), "gnome" (Gnome), "none" (other)
export OOO_FORCE_DESKTOP=none
# Permanently disable it by setting in the environment:
export JAVA_HOME=/nonexistent
# Others
export MAX_CONCURRENCY=1
export VCL_DEBUG_DISABLE_PDFCOMPRESSION=1
export VCL_DOUBLEBUFFERING_AVOID_PAINT=1
export VCL_DOUBLEBUFFERING_FORCE_ENABLE=1
export VCL_DOUBLEBUFFERING_ENABLE=1

export VCL_NO_THREAD_SCALE=1
export VCL_NO_THREAD_IMPORT=1
export EMF_PLUS_DISABLE=1
export EMF_PLUS_LIMIT=1

# Create the config
libreoffice25.2 -env:UserInstallation=file:///tmp/so-profile --headless --terminate_after_init


nano /tmp/so-profile/user/registrymodifications.xcu
nano /tmp/so-profile/user/config/javasettings_Linux_X86_64.xml

#<value>256m</value> <!-- initial heap size -->
#<value>1024m</value> <!-- maximum heap size -->

# https://wiki.documentfoundation.org/Development/Environment_variables
# https://wiki.openoffice.org/wiki/Environment_Variables

libreoffice --headless --convert-to pdf src/test.odt -env:UserInstallation=file:///tmp/so-profile

libreoffice25.2 \
    --invisible \
    --minimized \
    --headless \
    --nologo \
    --nofirststartwizard \
    --convert-to pdf src/test.odt \

libreoffice25.2 \
    --invisible \
    --minimized \
    --headless \
    --nologo \
    --nofirststartwizard \
    --convert-to pdf src/test.odt \
    -env:UserInstallation=file:///tmp/so-profile

```

## Profile

```sh

# Creamos el profile
libreoffice25.2 -env:UserInstallation=file:///tmp/so-profile --headless --terminate_after_init

libreoffice25.2 \
    --invisible \
    --minimized \
    --norestore \
    --headless \
    --nologo \
    --safe-mode \
    --nofirststartwizard \
    -env:UserInstallation=file:///tmp/so-profile \
    --accept="socket,host=localhost,port=2002;urp;StarOffice.ServiceManager"
```
