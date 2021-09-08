#!/bin/bash

files="${@:1}"
echo $files
#file=$1
#echo $file
#echo "git rm --force --cached --ignore-unmatch $file"
git filter-branch -f  --index-filter \
    "git rm --force --cached --ignore-unmatch $files" \
     -- --all
rm -Rf .git/refs/original && \
    git reflog expire --expire=now --all && \
    git gc --aggressive && \
    git prune
