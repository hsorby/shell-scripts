#!/bin/bash

# This scripts purpose is to create a release of libCellML.
# When creating an official release the project version will not be changed but the
# developer version will be set to empty.
# When **not** creating an official release the project version will not be changed but the
# developer version will be incremented by one for whatever the current pre release text is.
#
# This script has only been tested on macOS.
#
# Usage:
#  ./create-libcellml-release.sh <absolute-path-to-libcellml-source> [<github-token>] [release]
# 
repo_dir=$1
token=$2

if [ "x$3" == "xrelease" ]; then
  pre_release=false
else
  pre_release=true
fi
 
if [ -d "$repo_dir" ]; then
  cd $repo_dir
  git co main
  project_version=`perl -lne 'print $1 if /_PROJECT_VERSION (\d+.\d+.\d+)/' < CMakeLists.txt`
  pre_release_text=`perl -lne 'print $1 if /PROJECT_DEVELOPER_VERSION -([a-z]+).\d+/' < CMakeLists.txt`
  old_dev_version=`perl -lne 'print $1 if /PROJECT_DEVELOPER_VERSION -[a-z]+.(\d+)/' < CMakeLists.txt`

  new_version=$(($old_dev_version+1))
  old_string="PROJECT_DEVELOPER_VERSION -$pre_release_text.$old_dev_version"
  if [ "x$pre_release" == "xfalse" ]; then
    new_string="PROJECT_DEVELOPER_VERSION"
  else
    new_string="PROJECT_DEVELOPER_VERSION -$pre_release_text.$new_version"
  fi
  sed -i '' "s/$old_string/$new_string/" CMakeLists.txt

  full_version_string="$project_version-$pre_release_text.$new_version"

  git add CMakeLists.txt
  git ci -m "Setting version to $project_version-$pre_release_text.$new_version."
  git tag -a s$full_version_string -m "Source tag for version $full_version_string."
  git diff --binary release > release.patch  
  git co release
  git apply release.patch
  rm release.patch
  git add .
  git ci -m "Releasing version $full_version_string."
  git tag -a v$full_version_string -m "Version $full_version_string."
  git push prime --tags release
  
  # Do we need to sleep a bit to wait for the release to be ready?
  sleep 5
  data_string='{"tag_name": "v'$full_version_string'", "name": "v'$full_version_string'", "body": "Release v'$full_version_string' of the libCellML library.", "draft": false, "prerelease": '$pre_release'}'
  echo $data_string
  #git restore CMakeLists.txt
  if [ -d "$token" ]; then
    curl -s -H "Authorization: token $token" \
      -H "Accept: application/vnd.github.v3+json" \
      -d $data_string \
      "https://api.github.com/repos/cellml/libcellml/releases"
  fi
  git co main
fi

