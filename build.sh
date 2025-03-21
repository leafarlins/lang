#!/bin/bash

edit_changelog() {
    echo "Editting changelog"
    LASTHEAD=$(grep HEAD CHANGELOG.md)
    LASTV=$(echo $LASTHEAD | grep -Po "compare/\K(v[0-9]\.[0-9]*\.[0-9]*)")

    sed -i "s/$LASTV\.\./v$VERSAO\.\./" CHANGELOG.md
    sed -i "/^\[unreleased/a [${VERSAO/v/}]: https://github.com/leafarlins/lang/compare/$LASTV..$VERSAO/" CHANGELOG.md
    sed -i "/^### \[unreleased/a ## \[$VERSAO\] - $HOJE" CHANGELOG.md
    #sed -n '/## \[unreleased/,/^## /p' CHANGELOG.md | sed '/^## \[/d' > /tmp/tagnotes

    sed -i "s/langapp v.*/langapp v$VERSAO/" app/templates/about.html
}

commit_tag() {
    echo "Committing"
    git add CHANGELOG.md
    git add app/templates/about.html
    git commit -m "release v$VERSAO"
    git tag v$VERSAO
    git push --tags
    git push origin main

}

docker_build() {
    echo "Construindo container"
    docker build -t leafarlins/lang:v$VERSAO . || exit 1
    docker build -t leafarlins/lang:latest .
    docker push leafarlins/lang:v$VERSAO || exit 1
    docker push leafarlins/lang:latest || exit 1
}

VERSAO=$1
HOJE=$(date "+%Y-%m-%d")

echo "Building version $VERSAO"

edit_changelog
commit_tag
docker_build