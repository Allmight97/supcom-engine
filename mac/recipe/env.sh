# Source from the OpenSupCom checkout root. Build caches and temp files stay in its .local/.
export VCPKG_ROOT="$PWD/.local/vcpkg"
export VCPKG_DOWNLOADS="$VCPKG_ROOT/downloads"
export VCPKG_BINARY_SOURCES="clear;files,$PWD/.local/bincache,readwrite"
export VCPKG_DISABLE_METRICS=1
export TMPDIR="$PWD/.local/tmp"
export XDG_CACHE_HOME="$PWD/.local/cache"
export CLANG_MODULE_CACHE_PATH="$PWD/.local/cache/clang"
export PYTHONDONTWRITEBYTECODE=1
export OSC_FA_PATH="${OSC_FA_PATH:-$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/.." && pwd)/work/game}"
export VULKAN_SDK="${VULKAN_SDK:-$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/.." && pwd)/work/vulkan-sdk/1.4.363.0/macOS}"
