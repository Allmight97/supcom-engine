# Source from an OpenSupCom checkout root. Build temp files stay in its .local/. Every worktree of the repository
# shares the main checkout's vcpkg, binary cache, game files (mac/work/game) and Vulkan SDK.
here=$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)
toolkit=$(cd "$here/.." && pwd)
if [ "${here%/mac/recipe}" != "$here" ] && common=$(git -C "$here" rev-parse --path-format=absolute --git-common-dir 2>/dev/null); then
    toolkit=${common%/.git}/mac
fi
checkout=$(cd "$toolkit/.." && pwd)
export VCPKG_ROOT="${VCPKG_ROOT:-$checkout/.local/vcpkg}"
export VCPKG_DOWNLOADS="$VCPKG_ROOT/downloads"
export VCPKG_BINARY_SOURCES="clear;files,$checkout/.local/bincache,readwrite"
export VCPKG_DISABLE_METRICS=1
export TMPDIR="$PWD/.local/tmp"
export XDG_CACHE_HOME="$PWD/.local/cache"
export CLANG_MODULE_CACHE_PATH="$PWD/.local/cache/clang"
export PYTHONDONTWRITEBYTECODE=1
export OSC_FA_PATH="${OSC_FA_PATH:-$toolkit/work/game}"
export VULKAN_SDK="${VULKAN_SDK:-$toolkit/work/vulkan-sdk/1.4.363.0/macOS}"
