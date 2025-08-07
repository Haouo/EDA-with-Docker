#!/bin/bash

# handle xauth issue
XAUTH=".xauth/.xauth_temp"
mkdir -p .xauth && touch $XAUTH
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
chmod 666 $XAUTH
