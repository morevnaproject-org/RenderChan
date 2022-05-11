#!/bin/bash

set -e


if [ -z "$1" ]; then
	echo "USAGE: $0 VERSION"
	exit 1
fi

VERSION=$1

DIRNAME=`dirname "$0"`
cd ${DIRNAME}/..

git checkout -b "version-${VERSION}"

sed -i "s|__version__ = .*|__version__ = '${VERSION}'|" renderchan/core.py

git add renderchan/core.py
git commit -m "Version  ${VERSION}"
git push origin "version-${VERSION}"
git tag "v${VERSION}"
git push origin "refs/tags/v${VERSION}"
