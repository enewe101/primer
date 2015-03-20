#!/bin/bash

name=$1

find . -type f -exec sed -e 's/APP_NAME/'$name'/g' -i.bak '{}' +
find . -type f -name '*.bak' -delete
mv APP_NAME/static/APP_NAME APP_NAME/static/$name
mv APP_NAME/templates/APP_NAME APP_NAME/templates/$name
mv APP_NAME $name
