#!/bin/bash

variant=$1
independent=$2

if [ -z "$independent" ]
then
	postfix=$variant
else
	postfix=${variant}_independent
fi

cur_dir=$(pwd)
test_dir=${cur_dir}/opencmiss_$postfix
conf_dir=${cur_dir}/setup-build-$postfix

if [ -d $test_dir ]; then
	rm -rf $test_dir
fi

if [ -d $conf_dir ]; then
	rm -rf $conf_dir
fi

