#!/usr/bin/env bash
# Configure and build OpenSupCom (arm64 macOS) into build/play of the checkout at $OSC_ROOT
# (default: the checkout this mac/ folder sits in), with this folder's env.sh. Logs go to its .local/.
here=$(cd "$(dirname "$0")" && pwd)
cd "${OSC_ROOT:-$here/../..}" && source "$here/env.sh" || exit 1
mkdir -p .local/tmp || exit 1
step() {
    name=$1; shift
    echo "build: $name" >&2
    ( while sleep 600; do
        stats=$(ps -A -o pid=,ppid=,%cpu=,rss= | awk -v root=$$ '{ppid[$1]=$2; cpu[$1]=$3; rss[$1]=$4}
            END {for (p in ppid) {q=p; while (q in ppid && q != root) q=ppid[q]; if (q == root && p != root) {c+=cpu[p]; r+=rss[p]}}
                 printf "CPU %d%%, memory %d MB", c, r / 1024}')
        echo "build: $name, $((SECONDS / 60)) min elapsed, $stats" >&2
    done ) &
    beat=$!
    "$@" > ".local/$name.log" 2>&1
    status=$?
    pkill -P $beat; kill $beat; wait $beat 2>/dev/null
    return $status
}
step configure cmake -S . -B build/play -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" -DVCPKG_TARGET_TRIPLET=arm64-osx && echo CONFIGURE_OK || { echo CONFIGURE_FAIL; exit 1; }
step build cmake --build build/play -j 8 && echo BUILD_OK || { echo BUILD_FAIL; exit 1; }
