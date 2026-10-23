# Shared launcher for the capture tools: one way to start a game in the CrossOver bottle, wait for it,
# stop it and publish its log. Source from mac/ (the tools cd there first).
#   game_run_start KIND INIT LOG [GAME ARGS...]  KIND original (GOG game, 1680x1050 window) or faf (FAF's
#                                                game, 1024x768 window; GAME_RUN_WINDOW="W H" overrides);
#                                                the game logs to LOG.partial
#   game_run_wait_marker TEXT TIMEOUT [HOOK]     wait until LOG.partial contains TEXT, running HOOK each poll;
#                                                exit 1 after TIMEOUT seconds
#   game_run_wait_seconds N                      let the game run N seconds
#   game_run_wait_exit LIMIT                     wait for the game to exit; stop it after LIMIT seconds
#   game_run_finish                              stop the game and rename LOG.partial to LOG
#   game_run_shoot_ready PREFIX [SUFFIX]         for each new REFSHOT|READY|NAME line, save the unscaled game
#                                                window as PREFIXNAMESUFFIX.png (use as a wait hook);
#                                                sets GAME_RUN_SHOT_FAILED on a failed capture
#   game_run_prefs FILE                          use FILE as Game.prefs for this run (call before
#                                                game_run_start); the original is restored on exit
# A run that fails leaves only LOG.partial, so LOG always means a finished run. game_run_start refuses to
# start when LOG exists (a capture of the original cannot be redone: pick a new name); it replaces a leftover
# LOG.partial. It also:
#   - takes the bottle lock (mac/work/bottle.lock) before Game.prefs is touched, and an original-game run refuses
#     when active_mods names a mod the original would load (its Documents mods folder or gamedata/mods.scd);
#   - copies mac/tools/ and mac/agents/faf-autorun to mac/work/capture-run/NAME/ and runs the hooks from there, so editing
#     a hook mid-run changes nothing (GAME_RUN_DIR; a tool's generated init may point into it); a tool's own files from
#     elsewhere (staged probe sources) go in as GAME_RUN_STAGE=DIR, copied to GAME_RUN_DIR/stage (INIT "stage/init.lua");
#   - runs mac/tools/lib/capture.py's preflight every 5 s while waiting: stops on the first Lua error or unknown
#     unit type, a loaded hook without HOOKCHECK within 90 s, or a missed checkpoint (GAME_RUN_CHECKPOINTS,
#     "TEXT@TICK" separated by ";"; GAME_RUN_ALLOW lists tolerated error texts separated by ";").
# game_run_finish writes LOG's setup manifest, NAME.setup (capture.py setup).
# Progress goes to stderr: "game-run: PHASE" when a wait step starts, and every 10 minutes of waiting a line with
# the elapsed time and the game's CPU percent and resident memory. With GAME_RUN_WATCH=FILE the same lines (and the
# reason a run stops) are appended there, with the time, for a Monitor to follow.

GAME_RUN_PREFS="$HOME/Library/Application Support/CrossOver/Bottles/${FAF_BOTTLE:-SupCom}/drive_c/users/crossover/AppData/Local/Gas Powered Games/Supreme Commander Forged Alliance/Game.prefs"

game_run_say() {
    echo "game-run: $1" >&2
    [ -z "${GAME_RUN_WATCH:-}" ] || echo "$(date +%T) $1" >> "$GAME_RUN_WATCH"
}

game_run_phase() {
    game_run_say "$1"
    GAME_RUN_BEAT_AT=$(date +%s)
}

game_run_pattern() {
    printf '(SupremeCommander|ForgedAlliance)[.]exe.*%s' "$(game_run_winpath "$1" | sed 's/[][\\.*+?^$(){}|]/\\&/g')"
}

game_run_beat() {
    now=$(date +%s)
    [ $((now - GAME_RUN_BEAT_AT)) -ge 600 ] || return 0
    GAME_RUN_BEAT_AT=$now
    pid=$(pgrep -f "$GAME_RUN_PATTERN" | head -1)
    stats=$(ps -o %cpu=,rss= -p "${pid:-0}" 2>/dev/null | awk '{printf "CPU %s%%, memory %d MB", $1, $2 / 1024}')
    game_run_say "still waiting, $(( (now - GAME_RUN_T0) / 60 )) min elapsed${stats:+, $stats}"
}

game_run_winpath() {
    case "$1" in /*) set -- "$1" ;; *) set -- "$PWD/$1" ;; esac
    printf 'Z:%s' "$1" | tr / '\\'
}

game_run_stop() {
    [ -n "${GAME_RUN_PATTERN:-}" ] || return 0
    pkill -f "$GAME_RUN_PATTERN" 2>/dev/null || true
    [ -z "${GAME_RUN_JOB:-}" ] || { wait "$GAME_RUN_JOB" 2>/dev/null || true; GAME_RUN_JOB=; }
    sleep 2
    if pgrep -f "$GAME_RUN_PATTERN" >/dev/null; then
        game_run_say "the game survived; sending SIGKILL"
        pkill -9 -f "$GAME_RUN_PATTERN" 2>/dev/null || true
    fi
}

game_run_lock() {
    [ -z "${GAME_RUN_LOCKED:-}" ] || return 0
    waited=0
    until mkdir work/bottle.lock 2>/dev/null; do
        owner=$(cat work/bottle.lock/pid 2>/dev/null)
        if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then
            rm -rf work/bottle.lock
            continue
        fi
        [ "$waited" -lt 20 ] || { echo "The bottle is locked by process ${owner:-?} (mac/work/bottle.lock)." >&2; exit 1; }
        sleep 2; waited=$((waited + 2))
    done
    echo $$ > work/bottle.lock/pid
    GAME_RUN_LOCKED=1
    trap game_run_cleanup EXIT
}

game_run_snapshot() {
    [ -z "${GAME_RUN_DIR:-}" ] || return 0
    mkdir -p work/capture-run
    GAME_RUN_DIR=$(mktemp -d "$PWD/work/capture-run/$1.XXXXXX")
    mkdir -p "$GAME_RUN_DIR/agents"
    rsync -a --exclude __pycache__ --exclude '*.png' tools "$GAME_RUN_DIR/"
    cp -R agents/faf-autorun "$GAME_RUN_DIR/agents/"
    [ -z "${GAME_RUN_STAGE:-}" ] || cp -R "$GAME_RUN_STAGE" "$GAME_RUN_DIR/stage"
}

game_run_preflight() {
    set --
    IFS=';'
    for checkpoint in ${GAME_RUN_CHECKPOINTS:-}; do [ -z "$checkpoint" ] || set -- "$@" --checkpoint "$checkpoint"; done
    for allow in ${GAME_RUN_ALLOW:-Unable to reset selection sets}; do [ -z "$allow" ] || set -- "$@" --allow "$allow"; done
    unset IFS
    reason=$(python3 -I tools/lib/capture.py watch "$GAME_RUN_PARTIAL" "$GAME_RUN_DIR/preflight.json" "$@") \
        || { game_run_say "stopping the run: $reason"; exit 1; }
}

game_run_cleanup() {
    game_run_stop
    [ -z "${GAME_RUN_LOCKED:-}" ] || rm -rf work/bottle.lock
    if [ -n "${GAME_RUN_PREFS_BACKUP:-}" ] && [ -f "$GAME_RUN_PREFS_BACKUP" ]; then
        cp -p "$GAME_RUN_PREFS_BACKUP" "$GAME_RUN_PREFS" && rm -f "$GAME_RUN_PREFS_BACKUP"
        echo "game-run: Game.prefs restored" >&2
    fi
}

game_run_start() {
    kind=$1 init=$2 GAME_RUN_LOG=$3
    shift 3
    [ ! -e "$GAME_RUN_LOG" ] || { echo "game-run: $GAME_RUN_LOG already exists; a capture is never overwritten. Use a new name." >&2; exit 1; }
    GAME_RUN_PARTIAL="$GAME_RUN_LOG.partial"
    GAME_RUN_PATTERN=$(game_run_pattern "$GAME_RUN_PARTIAL")
    GAME_RUN_ARGS="$*" GAME_RUN_END=marker GAME_RUN_T0=$(date +%s)
    game_run_phase "starting $(basename "$GAME_RUN_LOG")"
    game_run_lock
    waited=0
    while pgrep -f '(SupremeCommander|ForgedAlliance)[.]exe' >/dev/null; do
        [ "$waited" -lt 20 ] || { echo "A game is already running." >&2; exit 1; }
        sleep 2; waited=$((waited + 2))
    done
    game_dir="$HOME/Library/Application Support/CrossOver/Bottles/${FAF_BOTTLE:-SupCom}/drive_c/GOG Games/Supreme Commander Forged Alliance"
    if [ "$kind" = original ] && ! mods=$(python3 -I tools/lib/capture.py mods "$GAME_RUN_PREFS" \
            "$HOME/Documents/My Games/Gas Powered Games/Supreme Commander Forged Alliance/mods" "$game_dir/gamedata/mods.scd"); then
        echo "game-run: Game.prefs activates mods the original game would load ($mods); an original-game" \
            "capture needs them off (JStar's data: ask the main session)." >&2
        exit 1
    fi
    game_run_snapshot "$(basename "$GAME_RUN_LOG" .log)"
    case "$init" in /*) ;; *) init="$GAME_RUN_DIR/$init" ;; esac
    mkdir -p "$(dirname "$GAME_RUN_LOG")"
    rm -f "$GAME_RUN_PARTIAL" "$GAME_RUN_DIR/preflight.json"
    root=$PWD
    case "$kind" in
        original)
            agents/faf-crossover original /init "$(game_run_winpath "$init")" /nomovie /windowed ${GAME_RUN_WINDOW:-1680 1050} \
                "$@" /log "$(game_run_winpath "$GAME_RUN_PARTIAL")" > /dev/null 2>&1 &
            GAME_RUN_JOB=$! ;;
        faf)
            initwin=$(game_run_winpath "$init") logwin=$(game_run_winpath "$GAME_RUN_PARTIAL")
            (cd "$HOME/.faforever/bin" && "$root/agents/faf-crossover" game "$HOME/.faforever/bin/ForgedAlliance.exe" \
                /init "$initwin" /nobugreport /nomovie /windowed ${GAME_RUN_WINDOW:-1024 768} /log "$logwin" "$@") &
            GAME_RUN_JOB=$! ;;
        *) echo "game-run: unknown kind $kind" >&2; exit 2 ;;
    esac
}

game_run_wait_marker() {
    text=$1 deadline=$(( $(date +%s) + $2 )) hook=${3:-}
    polls=0
    game_run_phase "waiting for '$text'"
    until grep -qF "$text" "$GAME_RUN_PARTIAL" 2>/dev/null; do
        [ "$(date +%s)" -lt "$deadline" ] || { game_run_say "No '$text' line after $2 s."; exit 1; }
        game_run_beat
        [ -z "$hook" ] || "$hook"
        polls=$((polls + 1))
        [ $((polls % 10)) -ne 0 ] || [ ! -f "$GAME_RUN_PARTIAL" ] || game_run_preflight
        sleep 0.5
    done
}

game_run_wait_seconds() {
    deadline=$(( $(date +%s) + $1 ))
    game_run_phase "running for $1 s"
    while [ "$(date +%s)" -lt "$deadline" ]; do
        game_run_beat
        game_run_preflight
        sleep 5
    done
}

game_run_wait_exit() {
    deadline=$(( $(date +%s) + $1 ))
    game_run_phase "waiting for the game to exit (limit $1 s)"
    sleep 5
    GAME_RUN_END=exit
    while pgrep -f "$GAME_RUN_PATTERN" >/dev/null; do
        game_run_beat
        [ ! -f "$GAME_RUN_PARTIAL" ] || game_run_preflight
        if [ "$(date +%s)" -ge "$deadline" ]; then
            echo "game-run: still running after $1 s; stopping it" >&2
            GAME_RUN_END="time limit"
            break
        fi
        sleep 2
    done
}

game_run_finish() {
    game_run_phase "finishing"
    game_run_stop
    python3 -I tools/lib/capture.py setup "$GAME_RUN_PARTIAL" "$GAME_RUN_DIR" "$GAME_RUN_END" -- $GAME_RUN_ARGS >/dev/null
    mv "$GAME_RUN_PARTIAL" "$GAME_RUN_LOG"
}

game_run_prefs() {
    game_run_lock
    GAME_RUN_PREFS_BACKUP="$GAME_RUN_PREFS.game-run-backup"
    cp -p "$GAME_RUN_PREFS" "$GAME_RUN_PREFS_BACKUP"
    cp "$1" "$GAME_RUN_PREFS"
}

game_run_shoot_ready() {
    prefix=$1 suffix=${2:-}
    [ -x work/game-window/winid ] && [ work/game-window/winid -nt agents/game-window/winid.swift ] \
        || { mkdir -p work/game-window && swiftc -O agents/game-window/winid.swift -o work/game-window/winid; }
    for shot in $(grep -o 'REFSHOT|READY|[A-Za-z0-9_-]*' "$GAME_RUN_PARTIAL" 2>/dev/null | cut -d'|' -f3); do
        case " ${GAME_RUN_SHOTS_DONE:-} " in *" $shot "*) continue ;; esac
        png="$prefix$shot$suffix.png"
        mkdir -p "$(dirname "$png")"
        rm -f "$png"
        for attempt in 1 2 3; do
            id=$({ work/game-window/winid SupremeCommander --all; work/game-window/winid ForgedAlliance --all; } | head -1 | awk '{print $1}')
            [ -n "$id" ] && screencapture -x -o -t png -l "$id" "$png.partial" 2>/dev/null && mv "$png.partial" "$png" && break
            echo "capture of $shot failed (attempt $attempt, window id '$id')" >&2
            sleep 1
        done
        if [ -f "$png" ]; then
            echo "$png: $(sips -g pixelWidth -g pixelHeight "$png" | awk '/pixel/ {printf "%s ", $2}')px"
        else
            echo "FAILED: $png" >&2
            GAME_RUN_SHOT_FAILED=1
        fi
        GAME_RUN_SHOTS_DONE="${GAME_RUN_SHOTS_DONE:-} $shot"
    done
}
