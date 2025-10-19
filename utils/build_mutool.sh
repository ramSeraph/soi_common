#!/bin/bash

set -e

[[ -e bin/mutool ]] && exit 0
script_dir=$(dirname "$0")
patch_file=${script_dir}/mupdf.patch
patch_file=$(realpath "$patch_file")
git clone https://github.com/ArtifexSoftware/mupdf
cd mupdf
git checkout 1.20.0-rc1
git submodule update --init
# pickup patch from same folder as the script
git apply $patch_file
make HAVE_X11=no HAVE_GLUT=no
mkdir -p ../bin
cp build/release/mutool ../bin/ 
cd ..
rm -rf mupdf/
