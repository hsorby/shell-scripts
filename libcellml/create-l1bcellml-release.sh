#!/bin/bash

repo_dir=$1

if [ -d "$repo_dir" ]; then
  cd $repo_dir
  project_version=`perl -lne 'print $1 if /_PROJECT_VERSION (\d.\d.\d)/' < CMakeLists.txt`
  old_version=`perl -lne 'print $1 if /PROJECT_DEVELOPER_VERSION -rc.(\d+)/' < CMakeLists.txt`
  new_version=$(($old_version+1))
  old_string="PROJECT_DEVELOPER_VERSION -rc.$old_version"
  new_string="PROJECT_DEVELOPER_VERSION -rc.$new_version"
  sed -i '' "s/$old_string/$new_string/" CMakeLists.txt
  git add CMakeLists.txt
  git ci -m "Setting version to $project_version-rc.$new_version."
  git tag -a v$project_version-rc.$new_version -m "Release v$project_version-rc.$new_version of the libCellML library."
  git push --tags origin develop

  full_version_string="$project_version-rc.$new_version"
  data_string='{"tag_name": "v'$full_version_string'","target_commitish": "develop","name": "v'$full_version_string'","body": "Release v'$full_version_string' of the libCellML library.","draft": false,"prerelease": true}'
  #echo $data_string
  #curl --data '{"tag_name": "v1.0.0","target_commitish": "master","name": "v1.0.0","body": "Release of version 1.0.0","draft": false,"prerelease": false}' https://api.github.com/repos/:owner/:repository/releases?access_token=:your_access_token
  #git restore CMakeLists.txt
fi

