# shellcheck shell=bash
# betterleaks 1.10 reads .betterleaks.toml only when told to, so its filters were silently ignored without this.
export BETTERLEAKS_CONFIG="${BETTERLEAKS_CONFIG:-$PWD/.betterleaks.toml}"
