#!/bin/sh

# remove installed gpio lib if installed
apt-get purge -y python3-rpi.gpio rpi.gpio-common || /bin/true

# install libs
python3 -m pip install --trusted-host pypi.org "RPi.GPIO==0.7.1"
if [ $? -ne 0 ]; then
    exit 1
fi

