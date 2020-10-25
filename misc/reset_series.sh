#!/bin/bash

stem=$1
shift;

directory=$(dirname $1)

count=0
for f in "$@"; do
  count=$((count+1))
  number=$(printf "%05d" $count)
  extension="${f##*.}"
  mv $f $directory/$stem-$number.$extension
done
