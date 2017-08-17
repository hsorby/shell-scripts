
====================
Setup Script Testing
====================

The scripts in this directory are used to help test the CMake setup script for creating new installations of OpenCMISS.

test_variant.sh
===============

This bash script sets up and runs a known variant that the setup script can run.  This script takes two arguments, the second argument is optional.  The first argument is the type of variant to test, one of; standard, dependencies, libraries, or cmake_modules.  The first argument is required.  The second argument indicates whether to test the independent roots variant of the first option.  Any value for the second argument is sufficient, as long as it does not evaluate to empty.

Place the test_variant.sh script into the directory where the variants are to be created.  It will then create directories for the variant under test as children of the current directory.  No other scenario has been tested when using this script.

Examples:

# Test the standard variant:
./test_variant.sh standard

# Test the independent roots dependencies variant:
./test_variant.sh dependencies ind

reset.sh
========

This bash script deletes all the generated output from the test_variant.sh bash script.  It takes the same arguments as the test_variant.sh script.

Place the reset.sh script into the same directory as the test_variant.sh script.  No other scenario has been tested when using this script.

Examples:

# Remove the standard variant:
./reset.sh standard

# Remove the independent roots libraries variant:
./reset.sh libraries ind

