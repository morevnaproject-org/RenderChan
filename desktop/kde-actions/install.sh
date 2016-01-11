#!/bin/bash

PREFIX=`dirname $0`
cd ${PREFIX}
PREFIX=`pwd`

mkdir -p "$HOME/.kde/share/kde4/services/ServiceMenus/" || true
cp $PREFIX/renderchan.desktop "$HOME/.kde/share/kde4/services/ServiceMenus/"
