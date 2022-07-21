#!/bin/bash

set -e

DIRNAME=`dirname "$0"`
cd ${DIRNAME}/..

VERSION=`cat renderchan/core.py | sed -n "s/__version__ = '\(.*\)'.*$/\1/p"`
if [ -z "${VERSION}" ]; then
    echo "ERROR: Cannot find version information."
    exit 1
fi

git checkout master
git merge --ff-only v${VERSION}
git push
git branch -d version-${VERSION}
git push origin :version-${VERSION}
