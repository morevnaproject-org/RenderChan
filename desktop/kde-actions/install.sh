#!/bin/bash

SCRIPTPATH=`dirname $0`
if [ -z $1 ]; then
PREFIX=/usr/local
else
PREFIX="$1"
fi

if [[ `id -u` == "0" ]]; then
DEST="$PREFIX/share/kde4/services/ServiceMenus"
else
DEST="$HOME/.kde/share/kde4/services/ServiceMenus/"
fi

mkdir -p "$DEST" || true
install -D -m 644 "$SCRIPTPATH/renderchan.desktop" "$DEST"
