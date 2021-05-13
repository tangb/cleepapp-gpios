#!/bin/sh

# install libs
python3 -m pip install --trusted-host pypi.org "RPi.GPIO==0.7.0"
if [ $? -ne 0 ]; then
    exit 1
fi

