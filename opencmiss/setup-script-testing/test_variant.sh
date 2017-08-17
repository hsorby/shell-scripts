#!/bin/bash

variant=$1
independent=$2

cur_dir=$(pwd)

if [ -z "$independent" ]
then
	postfix=$variant
else
	postfix=${variant}_independent
fi

test_dir=${cur_dir}/opencmiss_$postfix/
conf_dir=${cur_dir}/setup-build-$postfix/
setup_dir=${cur_dir}/setup/

if [ -d $setup_dir ]
then
	cd $setup_dir
	git pull origin testing
else
	git clone git@github.com:hsorby/OpenCMISS-Setup.git -b testing setup
fi

if [ ! -d $conf_dir ]
then
	mkdir $conf_dir
fi
cd $conf_dir

case $variant in
	standard )
		if [ -z "$independent" ]
		then
			if [ ! -d $test_dir ]
			then
				mkdir $test_dir
			fi
			cmake -DOPENCMISS_ROOT=$test_dir $setup_dir
		else
			libs_dir=${test_dir}/libs
			deps_dir=${test_dir}/deps
			mods_dir=${test_dir}/mods
			mans_dir=${test_dir}/mans
			exas_dir=${test_dir}/exas
			if [ ! -d $test_dir ]
			then
				mkdir $test_dir
				mkdir $libs_dir
				mkdir $deps_dir
				mkdir $mods_dir
				mkdir $mans_dir
				mkdir $exas_dir
			fi
			cmake -DOPENCMISS_MANAGE_ROOT=$mans_dir -DOPENCMISS_CMAKE_MODULES_ROOT=$mods_dir -DOPENCMISS_DEPENDENCIES_ROOT=$deps_dir -DOPENCMISS_EXAMPLES_ROOT=$exas_dir -DOPENCMISS_LIBRARIES_ROOT=$libs_dir -DOPENCMISS_INDEPENDENT=TRUE $setup_dir
		fi
		;;
	arch_path )
		if [ ! -d $test_dir ]
		then
			mkdir $test_dir
		fi
		cmake -DOPENCMISS_ROOT=$test_dir -DOPENCMISS_MULTI_ARCHITECTURE=TRUE $setup_dir
		;;
	dependencies)
		if [ -z "$independent" ]
		then
			if [ ! -d $test_dir ]
			then
				mkdir $test_dir
			fi
			cmake -DOPENCMISS_SETUP_TYPE=dependencies -DOPENCMISS_DEPENDENCIES_ROOT=$test_dir $setup_dir
		else
			deps_dir=${test_dir}/deps
			mods_dir=${test_dir}/mods
			mans_dir=${test_dir}/mans
			if [ ! -d $test_dir ]
			then
				mkdir $test_dir
				mkdir $deps_dir
				mkdir $mods_dir
				mkdir $mans_dir
			fi
			cmake -DOPENCMISS_INDEPENDENT=TRUE -DOPENCMISS_SETUP_TYPE=dependencies -DOPENCMISS_DEPENDENCIES_ROOT=$deps_dir -DOPENCMISS_MANAGE_ROOT=$mans_dir -DOPENCMISS_CMAKE_MODULES_ROOT=$mods_dir $setup_dir
		fi
		;;
	cmake_modules)
		if [ ! -d $test_dir ]
		then
			mkdir $test_dir
		fi
		cmake -DOPENCMISS_SETUP_TYPE=cmake_modules -DOPENCMISS_CMAKE_MODULES_ROOT=$test_dir $setup_dir
		;;
	libraries)
		if [ -z "$independent" ]
		then
			if [ ! -d $test_dir ]
			then
				mkdir $test_dir
			fi
			cmake -DOPENCMISS_SETUP_TYPE=libraries -DOPENCMISS_LIBRARIES_ROOT=$test_dir -DOPENCMISS_DEPENDENCIES_INSTALL_PREFIX=/Users/hsor001/work/opencmiss-software/test_zone/opencmiss_dependencies/install/ -DOPENCMISS_CMAKE_MODULE_PATH=/Users/hsor001/work/opencmiss-software/test_zone/opencmiss_dependencies/install/share/cmake/ $setup_dir
		else
			zinc_dir=${test_dir}/zinc
			iron_dir=${test_dir}/iron
			mans_dir=${test_dir}/mans
			if [ ! -d $test_dir ]
			then
				mkdir $test_dir
				mkdir $zinc_dir
				mkdir $iron_dir
				mkdir $mans_dir
			fi

		fi
			cmake -DOPENCMISS_SETUP_TYPE=libraries -DOPENCMISS_INDEPENDENT=TRUE -DOPENCMISS_ZINC_ROOT=$zinc_dir -DOPENCMISS_IRON_ROOT=$iron_dir -DOPENCMISS_MANAGE_ROOT=$mans_dir -DOPENCMISS_DEPENDENCIES_INSTALL_PREFIX=/Users/hsor001/work/opencmiss-software/test_zone/opencmiss_dependencies/install/ -DOPENCMISS_CMAKE_MODULE_PATH=/Users/hsor001/work/opencmiss-software/test_zone/opencmiss_dependencies/install/share/cmake/ $setup_dir
		;;
	* )
		echo "Unknown variant: $variant"
		exit 1
		;;
esac

cmake --build .
cd $cur_dir

