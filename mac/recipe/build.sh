#!/usr/bin/env bash
# Configure and build OpenSupCom (arm64 macOS) into build/play of the checkout at $OSC_ROOT
# (default: the checkout this mac/ folder sits in), with this folder's env.sh. Logs go to its .local/.
here=$(cd "$(dirname "$0")" && pwd)
cd "${OSC_ROOT:-$here/../..}" && source "$here/env.sh" || exit 1
mkdir -p .local/tmp || exit 1
cmake -S . -B build/play -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" -DVCPKG_TARGET_TRIPLET=arm64-osx > .local/configure.log 2>&1 && echo CONFIGURE_OK || { echo CONFIGURE_FAIL; exit 1; }
cmake --build build/play -j 8 > .local/build.log 2>&1 && echo BUILD_OK || { echo BUILD_FAIL; exit 1; }
