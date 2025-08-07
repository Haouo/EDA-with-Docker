#!/bin/bash

# handle xauth issue
XAUTH=".xauth_temp"
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
chmod 666 $XAUTH
