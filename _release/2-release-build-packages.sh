#!/bin/bash

set -e

DIRNAME=`dirname "$0"`
cd ${DIRNAME}/..
SOURCES_DIR=`pwd`

if ! ( which makensis > /dev/null ); then
    echo
    echo "ERROR: Cannot find makensis command!"
    echo "Please install NSIS package."
    echo
    exit 1
fi

[ -d "${SOURCES_DIR}/_release/files" ] || mkdir -p "${SOURCES_DIR}/_release/files"
[ -d "${SOURCES_DIR}/_release/files.tmp" ] || mkdir -p "${SOURCES_DIR}/_release/files.tmp"

VERSION=`cat renderchan/core.py | sed -n "s/__version__ = '\(.*\)'.*$/\1/p"`
if [ -z "${VERSION}" ]; then
    echo "ERROR: Cannot find version information."
    exit 1
fi

foreachfile() {
    local DIR="$1"
    local COMMAND="$2"
    if [ -z "$DIR" ] || [ ! -e "$DIR" ]; then
        return 1
    fi
        
    if [ -d "$DIR" ]; then
        for FILE in "$DIR/".*; do
            if [ "$FILE" != "$DIR/." ] && [ "$FILE" != "$DIR/.." ]; then
                if ! "$COMMAND" "$FILE" ${@:3}; then
                    return 1
                fi
            fi
        done
        for FILE in "$DIR/"*; do
            if [ "$FILE" != "$DIR" ] && [ "$FILE" != "$DIR/" ]; then
                if ! "$COMMAND" "$FILE" ${@:3}; then
                    return 1
                fi
            fi
        done
    fi
}

nsis_register_file() {
    FILE=$1
    WIN_FILE=$(echo "$FILE" | sed "s|\/|\\\\|g")
    ! [ -L "$FILE" ] || return 0

    if [[ "$FILE" != ./* ]]; then
        foreachfile $FILE nsis_register_file
    elif [ "${FILE:0:8}" = "./files-" ]; then
        true # skip
    else
        local TARGET_INSTALL="files-install.nsh"
        local TARGET_UNINSTALL="files-uninstall.nsh"

        if [ -d "$FILE" ]; then
            echo "CreateDirectory \"\$INSTDIR\\${WIN_FILE:2}\""     >> "$TARGET_INSTALL"
            foreachfile "$FILE" nsis_register_file
            echo "RMDir \"\$INSTDIR\\${WIN_FILE:2}\""               >> "$TARGET_UNINSTALL" 
        else
            echo "File \"/oname=${WIN_FILE:2}\" \"${WIN_FILE:2}\""  >> "$TARGET_INSTALL"
            echo "Delete \"\$INSTDIR\\${WIN_FILE:2}\""              >> "$TARGET_UNINSTALL" 
        fi
    fi
}

cd "${SOURCES_DIR}/_release/files.tmp"

# Linux
[ ! -d renderchan-${VERSION} ] || rm -rf renderchan-${VERSION}
mkdir renderchan-${VERSION}
cp -rf ../../.git renderchan-${VERSION}/
pushd renderchan-${VERSION}/
git reset --hard
rm -rf .git
rm -rf _release
popd
[ ! -f ../files/renderchan-${VERSION}-linux.tar.bz2 ] || rm -f ../files/renderchan-${VERSION}-linux.tar.bz2
tar -cjf ../files/renderchan-${VERSION}-linux.tar.bz2 renderchan-${VERSION}
rm -rf renderchan-${VERSION}

# Windows
[ -f "renderchan-1.0-alpha1-win.zip" ] || wget https://github.com/morevnaproject-org/RenderChan/releases/download/v1.0-alpha1/renderchan-1.0-alpha1-win.zip
[ ! -d renderchan-1.0-alpha1 ] || rm -rf renderchan-1.0-alpha1
unzip renderchan-1.0-alpha1-win.zip
[ ! -d renderchan-${VERSION} ] || rm -rf renderchan-${VERSION}
mv renderchan-1.0-alpha1 renderchan-${VERSION}
rm -rf renderchan-${VERSION}/renderchan
mkdir renderchan-${VERSION}/renderchan
cp -rf ../../.git renderchan-${VERSION}/renderchan
pushd renderchan-${VERSION}/renderchan
git reset --hard
rm -rf .git
rm -rf _release
popd
rm -rf renderchan-${VERSION}/env
mv renderchan-${VERSION}/renderchan/env/windows renderchan-${VERSION}/env
rm -rf renderchan-${VERSION}/renderchan/env

rm -rf renderchan-${VERSION}/python
mkdir renderchan-${VERSION}/python
[ -f "python-3.8.10-embed-win32.zip" ] || wget https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-win32.zip
cd renderchan-${VERSION}/python
unzip ../../python-3.8.10-embed-win32.zip
cd ../..
[ -f renderchan-${VERSION}/renderchan/desktop/renderchan.ico ] || cp -f ../../desktop/renderchan.ico renderchan-${VERSION}/renderchan/desktop/renderchan.ico

cd renderchan-${VERSION}/
[ ! -f ../../files/renderchan-${VERSION}.exe ] || rm -f ../../files/renderchan-${VERSION}.exe
TARGET_INSTALL="files-install.nsh"
TARGET_UNINSTALL="files-uninstall.nsh"
[ ! -f ${TARGET_INSTALL} ] || rm -f ${TARGET_INSTALL}
[ ! -f ${TARGET_UNINSTALL} ] || rm -f ${TARGET_UNINSTALL}
touch ${TARGET_INSTALL}
touch ${TARGET_UNINSTALL}
for FILE in `find . -print`; do
    WIN_FILE=$(echo "$FILE" | sed "s|\/|\\\\|g")
    if [ "${FILE}" = "./${TARGET_INSTALL}" ]; then
        true
    elif [ "${FILE}" = "./${TARGET_UNINSTALL}" ]; then
        true
    elif [ -d "$FILE" ]; then
	echo "CreateDirectory \"\$INSTDIR\\${WIN_FILE:2}\""     >> "$TARGET_INSTALL"
	echo "RMDir \"\$INSTDIR\\${WIN_FILE:2}\""               >> "$TARGET_UNINSTALL" 
    else
	echo "File \"/oname=${WIN_FILE:2}\" \"${WIN_FILE:2}\""  >> "$TARGET_INSTALL"
	echo "Delete \"\$INSTDIR\\${WIN_FILE:2}\""              >> "$TARGET_UNINSTALL" 
    fi
done
[ ! -f config.nsh ] || rm -f config.nsh
ARCH=32
cat > config.nsh << EOF
!define PK_NAME          "renderchan" 
!define PK_DIR_NAME      "RenderChan"
!define PK_NAME_FULL     "RenderChan"
!define PK_ARCH          "${ARCH}"
!define PK_VERSION       "${VERSION}"
!define PK_VERSION_FULL  "${VERSION}"
!define PK_EXECUTABLE    "renderchan-cli.bat"
!define PK_ICON          "renderchan\\desktop\\renderchan.ico"
!define PK_DOCUMENT_ICON "share\\pixmaps\\sif_icon.ico"
!define PK_LICENSE       ".\\renderchan\\LICENSE"
EOF
cp "../../renderchan.nsi" ./
makensis renderchan.nsi
mv renderchan-${VERSION}.exe ../../files/
rm *.nsh
rm renderchan.nsi
cd ..

[ ! -f ../files/renderchan-${VERSION}-win.zip ] || rm -f ../files/renderchan-${VERSION}-win.zip
zip -r ../files/renderchan-${VERSION}-win.zip renderchan-${VERSION}/

rm -rf renderchan-${VERSION}
