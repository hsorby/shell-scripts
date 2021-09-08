#!/bin/bash

target=$1

git filter-branch --tree-filter "rm -rf $target" --prune-empty HEAD
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

git commit -m "Removing $target from git history."
git gc

