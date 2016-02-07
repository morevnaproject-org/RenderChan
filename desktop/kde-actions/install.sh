#!/bin/bash

SCRIPTPATH=`dirname $0`
if [ -z $1 ]; then
PREFIX=/usr/local
else
PREFIX="$1"
fi

if [[ `id -u` == "0" ]]; then
DEST1="$PREFIX/share/kde4/services/ServiceMenus/"
DEST2="$PREFIX/share/kservices5/ServiceMenus/"
DEST3="$PREFIX/share/kservicetypes5/"
else
DEST1="$HOME/.kde/share/kde4/services/ServiceMenus/"
DEST2="$HOME/.local/share/kservices5/ServiceMenus/"
DEST3="$HOME/.local/share/kservicetypes5/"
fi

mkdir -p "$DEST1" || true
mkdir -p "$DEST2" || true
install -D -m 644 "$SCRIPTPATH/renderchan.desktop" "$DEST1"
install -D -m 644 "$SCRIPTPATH/renderchan.desktop" "$DEST2"

if [ ! -f "/usr/share/kservicetypes5/konqpopupmenuplugin.desktop" ] && \
   [ ! -f "/usr/local/share/kservicetypes5/konqpopupmenuplugin.desktop" ] && \
   [ ! -f "$HOME/.local/share/kservicetypes5/konqpopupmenuplugin.desktop" ]
then
    [ -d "$DEST3" ] || mkdir -p "$DEST3"
    install -D -m 644 "$SCRIPTPATH/konqpopupmenuplugin.desktop" "$DEST3"
fi
