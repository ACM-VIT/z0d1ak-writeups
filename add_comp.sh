#!/usr/bin/env bash
set -euo pipefail

# ─── colour helpers ──────────────────────────────────────────────────────────
red()     { printf '\033[0;31m%s\033[0m\n' "$*"; }
green()   { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow()  { printf '\033[0;33m%s\033[0m\n' "$*"; }
cyan()    { printf '\033[0;36m%s\033[0m\n' "$*"; }
bold()    { printf '\033[1m%s\033[0m\n'    "$*"; }
dim()     { printf '\033[2m%s\033[0m\n'    "$*"; }
boldcyan(){ printf '\033[1;36m%s\033[0m\n' "$*"; }

require() {
    local missing=0
    for cmd in "$@"; do
        if ! command -v "$cmd" &>/dev/null; then
            red "Required tool not found: $cmd"
            missing=1
        fi
    done
    if [[ $missing -eq 1 ]]; then
        red "Please install the missing tools and try again."
        exit 1
    fi
}

require curl jq

# ─── resolve repo root (where the script lives) ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CATEGORIES_FILE="${SCRIPT_DIR}/categories.txt"

# ─── input ───────────────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    red "Usage: $0 <ctftime_event_url>"
    echo "  e.g. $0 https://ctftime.org/event/3171/"
    exit 1
fi

CTFTIME_URL="${1%/}"
EVENT_ID="${CTFTIME_URL##*/}"

if ! [[ "$EVENT_ID" =~ ^[0-9]+$ ]]; then
    red "Could not parse event ID from URL: $CTFTIME_URL"
    exit 1
fi

# ─── fetch event metadata ─────────────────────────────────────────────────────
bold "Fetching event metadata from CTFtime API..."
API_URL="https://ctftime.org/api/v1/events/${EVENT_ID}/"

EVENT_JSON=$(curl -fsSL \
    -H "User-Agent: Mozilla/5.0 (compatible; ctf-setup-script/1.0)" \
    "$API_URL") || { red "Failed to fetch event data from $API_URL"; exit 1; }

TITLE=$(echo "$EVENT_JSON"        | jq -r '.title')
CTF_URL=$(echo "$EVENT_JSON"      | jq -r '.url')
START=$(echo "$EVENT_JSON"        | jq -r '.start')
FINISH=$(echo "$EVENT_JSON"       | jq -r '.finish')
FORMAT=$(echo "$EVENT_JSON"       | jq -r '.format')
PARTICIPANTS=$(echo "$EVENT_JSON" | jq -r '.participants')
DESCRIPTION=$(echo "$EVENT_JSON"  | jq -r '.description')
RESTRICTIONS=$(echo "$EVENT_JSON" | jq -r '.restrictions')
LOCATION=$(echo "$EVENT_JSON"     | jq -r '.location')
WEIGHT=$(echo "$EVENT_JSON"       | jq -r '.weight')
ONSITE=$(echo "$EVENT_JSON"       | jq -r '.onsite')
LIVE_FEED=$(echo "$EVENT_JSON"    | jq -r '.live_feed')

DISCORD_LINK=$(echo "$EVENT_JSON" | jq -r '[.description, .prizes] | join(" ")' \
    | grep -oP 'https://discord\.gg/\S+' | head -1 || true)

echo ""
boldcyan "══════════════════════════════════════════════"
boldcyan "  $TITLE"
boldcyan "══════════════════════════════════════════════"
printf "  %-14s %s\n" "CTFtime:"     "$CTFTIME_URL"
printf "  %-14s %s\n" "Website:"     "$CTF_URL"
printf "  %-14s %s (%s)\n" "Format:" "$FORMAT" "$RESTRICTIONS"
printf "  %-14s %s\n" "Start:"       "$START"
printf "  %-14s %s\n" "End:"         "$FINISH"
echo ""

# ─── create folder ───────────────────────────────────────────────────────────
FOLDER_NAME="$TITLE"
if [[ -d "${SCRIPT_DIR}/${FOLDER_NAME}" ]]; then
    yellow "Directory '$FOLDER_NAME' already exists, continuing into it."
else
    mkdir -p "${SCRIPT_DIR}/${FOLDER_NAME}"
    green "Created directory: $FOLDER_NAME"
fi
cd "${SCRIPT_DIR}/${FOLDER_NAME}"

# ─── CTFd? ───────────────────────────────────────────────────────────────────
echo ""
bold "Is this CTF using CTFd? (check ${CTF_URL}settings)"
printf "Uses CTFd? [y/N]: "
read -r USES_CTFD
USES_CTFD="${USES_CTFD,,}"

TOKEN=""
BASE_URL=""

if [[ "$USES_CTFD" == "y" || "$USES_CTFD" == "yes" ]]; then
    printf "CTFd base URL [%s]: " "$CTF_URL"
    read -r BASE_URL_INPUT
    BASE_URL="${BASE_URL_INPUT:-$CTF_URL}"
    BASE_URL="${BASE_URL%/}"

    printf "Player API token (leave blank to skip): "
    read -r TOKEN
fi

# ─── write README.md ──────────────────────────────────────────────────────────
README="README.md"
{
    echo "# $TITLE"
    echo ""
    echo "| Field        | Value |"
    echo "|--------------|-------|"
    echo "| CTFtime      | $CTFTIME_URL |"
    echo "| Website      | $CTF_URL |"
    echo "| Format       | $FORMAT |"
    echo "| Restrictions | $RESTRICTIONS |"
    echo "| Onsite       | $ONSITE |"
    echo "| Location     | ${LOCATION:-N/A} |"
    echo "| Weight       | $WEIGHT |"
    echo "| Start        | $START |"
    echo "| End          | $FINISH |"
    echo "| Participants | $PARTICIPANTS |"
    [[ -n "$DISCORD_LINK" ]] && echo "| Discord      | $DISCORD_LINK |"
    [[ -n "$LIVE_FEED" && "$LIVE_FEED" != "null" ]] && echo "| Live Feed    | $LIVE_FEED |"
    echo "| CTFd         | ${USES_CTFD:-no} |"
    echo ""
    echo "## Description"
    echo ""
    echo "$DESCRIPTION"
    echo ""
} > "$README"

green "Wrote $README"

# ─── interactive category picker ─────────────────────────────────────────────
# Usage: category_picker <nameref_result_array> <default_categories_array_nameref>
# Draws a checkbox list; Space toggles, A selects all, N deselects all, Enter confirms.
category_picker() {
    # $1 = name of result array, $2 = name of source array
    local -n _result="$1"
    local -n _source="$2"
    local count=${#_source[@]}

    if [[ $count -eq 0 ]]; then
        _result=()
        return
    fi

    # selected[i]=1 means checked
    local selected=()
    for (( i=0; i<count; i++ )); do selected+=("1"); done

    local cursor=0

    # hide cursor
    tput civis 2>/dev/null || true

    local old_tty tty_cleanup_installed=0
    old_tty=$(stty -g)

    _restore_picker_terminal() {
        # Fallback to 'stty sane' if the local variable dropped out of scope
        if [[ -n "${old_tty:-}" ]]; then
            stty "$old_tty" 2>/dev/null || true
        else
            stty sane 2>/dev/null || true
        fi
        tput rmcup 2>/dev/null || true
        tput cnorm 2>/dev/null || true
    }

    _picker_on_exit() {
        _restore_picker_terminal
        exit 130
    }

    trap '_picker_on_exit' EXIT INT TERM
    tty_cleanup_installed=1

    # use the terminal's alternate screen/cursor controls where available
    tput smcup 2>/dev/null || true
    stty -echo -icanon min 1 time 0

    _draw_picker() {
        local i
        tput cup 0 0 2>/dev/null || printf '\033[H'
        tput ed 2>/dev/null || printf '\033[J'

        printf '\033[1;36m── Select categories from defaults ─────────────────\033[0m\n'
        printf '\033[2m  ↑/↓ move  Space toggle  a all  n none  Enter confirm\033[0m\n\n'

        for (( i=0; i<count; i++ )); do
            local prefix="  "
            [[ $i -eq $cursor ]] && prefix="> "
            local box="[ ]"
            [[ "${selected[$i]}" == "1" ]] && box="[✓]"

            if [[ $i -eq $cursor ]]; then
                printf '\033[1;36m%s %s  %s\033[0m\n' "$prefix" "$box" "${_source[$i]}"
            else
                printf '%s %s  %s\n' "$prefix" "$box" "${_source[$i]}"
            fi
        done
    }

    local i

    _draw_picker

    while true; do
        local key seq

        IFS= read -rsn1 key </dev/tty || key=''

        if [[ "$key" == $'\033' ]]; then
            read -rsn2 -t 1 seq </dev/tty || seq=''
            key=$'\033'"$seq"
        fi

        case "$key" in
            $'\033[A'|$'\033OA'|$'\033[1A'|$'\033[1;*A'|'k'|'K')
                # Fixed: using explicit assignment to avoid bash arithmetic exit codes
                if (( cursor > 0 )); then cursor=$((cursor - 1)); fi
                ;;
            $'\033[B'|$'\033OB'|$'\033[1B'|$'\033[1;*B'|'j'|'J')
                # Fixed: using explicit assignment to avoid bash arithmetic exit codes
                if (( cursor < count-1 )); then cursor=$((cursor + 1)); fi
                ;;
            ' ')
                if [[ "${selected[$cursor]}" == "1" ]]; then
                    selected[$cursor]="0"
                else
                    selected[$cursor]="1"
                fi
                ;;
            'a'|'A')
                for (( i=0; i<count; i++ )); do selected[$i]="1"; done
                ;;
            'n'|'N')
                for (( i=0; i<count; i++ )); do selected[$i]="0"; done
                ;;
            $'\r'|$'\n'|'')
                break
                ;;
        esac

        _draw_picker
    done

    if [[ $tty_cleanup_installed -eq 1 ]]; then
        trap - EXIT INT TERM
    fi
    _restore_picker_terminal

    printf '\n'

    # collect results
    _result=()
    for (( i=0; i<count; i++ )); do
        [[ "${selected[$i]}" == "1" ]] && _result+=("${_source[$i]}")
    done
}

# ─── category folders (non-CTFd path only) ───────────────────────────────────
if [[ "$USES_CTFD" != "y" && "$USES_CTFD" != "yes" ]]; then

    # ── load defaults ──
    DEFAULT_CATEGORIES=()
    if [[ -f "$CATEGORIES_FILE" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ -z "$line" ]] && continue
            DEFAULT_CATEGORIES+=("$line")
        done < "$CATEGORIES_FILE"
    else
        yellow "categories.txt not found at $CATEGORIES_FILE, starting with empty list."
    fi

    # ── pick from defaults ──
    echo ""
    boldcyan "── Select categories from defaults ─────────────────"
    dim   "  (Space = toggle, a = all, n = none, Enter = confirm)"
    echo ""

    PICKED_DEFAULTS=()
    if [[ ${#DEFAULT_CATEGORIES[@]} -gt 0 ]]; then
        category_picker PICKED_DEFAULTS DEFAULT_CATEGORIES
    else
        yellow "  No default categories found."
    fi

    # ── extra categories ──
    echo ""
    bold "Add extra categories? (comma-separated, leave blank to skip):"
    printf "  > "
    read -r EXTRA_INPUT

    EXTRA_CATEGORIES=()
    if [[ -n "$EXTRA_INPUT" ]]; then
        IFS=',' read -ra RAW_EXTRA <<< "$EXTRA_INPUT"
        for e in "${RAW_EXTRA[@]}"; do
            # trim leading/trailing whitespace, preserve rest of capitalisation
            e="$(echo "$e" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
            [[ -n "$e" ]] && EXTRA_CATEGORIES+=("$e")
        done
    fi

    # ── build final list ──
    FINAL_CATEGORIES=("${PICKED_DEFAULTS[@]}" "${EXTRA_CATEGORIES[@]}")

    # ── make dirs ──
    if [[ ${#FINAL_CATEGORIES[@]} -gt 0 ]]; then
        for cat in "${FINAL_CATEGORIES[@]}"; do
            mkdir -p "$cat"
        done
        echo ""
        green "Created category folders:"
        for cat in "${FINAL_CATEGORIES[@]}"; do
            printf "  \033[0;32m+\033[0m %s\n" "$cat"
        done
    else
        yellow "No categories selected — no folders created."
    fi
fi

# ─── CTFd challenge fetch ─────────────────────────────────────────────────────
if [[ "$USES_CTFD" == "y" || "$USES_CTFD" == "yes" ]] && [[ -n "$TOKEN" ]]; then
    bold "\nFetching challenge list from CTFd..."

    CHALLENGES_JSON=$(curl -fsSL \
        -X GET "${BASE_URL}/api/v1/challenges" \
        -H "Authorization: Token ${TOKEN}" \
        -H "Content-Type: application/json") || {
        red "Failed to fetch challenges from ${BASE_URL}/api/v1/challenges"
        exit 1
    }

    SUCCESS=$(echo "$CHALLENGES_JSON" | jq -r '.success')
    if [[ "$SUCCESS" != "true" ]]; then
        red "CTFd API returned an error:"
        echo "$CHALLENGES_JSON" | jq .
        exit 1
    fi

    mapfile -t API_CATEGORIES < <(echo "$CHALLENGES_JSON" | jq -r '.data[].category' | sort -u)
    green "Categories found: ${API_CATEGORIES[*]}"
    for cat in "${API_CATEGORIES[@]}"; do
        mkdir -p "$cat"
        green "  Created category folder: $cat"
    done

    mapfile -t CHALLENGE_IDS < <(echo "$CHALLENGES_JSON" | jq -r '.data[].id')

    for CID in "${CHALLENGE_IDS[@]}"; do
        bold "  Fetching challenge #${CID}..."

        CHAL_JSON=$(curl -fsSL \
            -X GET "${BASE_URL}/api/v1/challenges/${CID}" \
            -H "Authorization: Token ${TOKEN}" \
            -H "Content-Type: application/json") || {
            yellow "  Failed to fetch challenge #${CID}, skipping."
            continue
        }

        C_SUCCESS=$(echo "$CHAL_JSON" | jq -r '.success')
        if [[ "$C_SUCCESS" != "true" ]]; then
            yellow "  Challenge #${CID} returned error, skipping."
            continue
        fi

        C_NAME=$(echo "$CHAL_JSON"   | jq -r '.data.name')
        C_CAT=$(echo "$CHAL_JSON"    | jq -r '.data.category')
        C_VALUE=$(echo "$CHAL_JSON"  | jq -r '.data.value')
        C_DESC=$(echo "$CHAL_JSON"   | jq -r '.data.description')
        C_SOLVES=$(echo "$CHAL_JSON" | jq -r '.data.solves')
        C_CONN=$(echo "$CHAL_JSON"   | jq -r '.data.connection_info')
        C_SOLVED=$(echo "$CHAL_JSON" | jq -r '.data.solved_by_me')

        if [[ "$C_SOLVED" != "true" ]]; then
            yellow "  Challenge #${CID} ($C_NAME) not solved by team, skipping."
            continue
        fi

        mapfile -t C_FILES < <(echo "$CHAL_JSON" | jq -r '.data.files[]? // empty')
        mapfile -t C_TAGS  < <(echo "$CHAL_JSON" | jq -r '.data.tags[]? // empty')

        CHAL_PATH="${C_CAT}/${C_NAME}"
        mkdir -p "$CHAL_PATH"

        CHAL_README="${CHAL_PATH}/README.md"
        {
            echo "# $C_NAME"
            echo ""
            echo "| Field      | Value |"
            echo "|------------|-------|"
            echo "| Category   | $C_CAT |"
            echo "| Points     | $C_VALUE |"
            echo "| Solves     | $C_SOLVES |"
            if [[ "${#C_TAGS[@]}" -gt 0 && -n "${C_TAGS[0]}" ]]; then
                TAGS_STR=$(IFS=', '; echo "${C_TAGS[*]}")
                echo "| Tags       | $TAGS_STR |"
            fi
            if [[ "$C_CONN" != "null" && -n "$C_CONN" ]]; then
                echo "| Connection | $C_CONN |"
            fi
            echo ""
            echo "## Description"
            echo ""
            echo "$C_DESC"
            echo ""
            if [[ "${#C_FILES[@]}" -gt 0 && -n "${C_FILES[0]}" ]]; then
                echo "## Files"
                echo ""
                for f in "${C_FILES[@]}"; do
                    FILE_NAME=$(basename "$(echo "$f" | cut -d'?' -f1)")
                    echo "- [$FILE_NAME](./$FILE_NAME)"
                done
                echo ""
            fi
            echo "## Writeup"
            echo ""
            echo "### Flag"
            echo ""
            echo "\`\`\`"
            echo ""
            echo "\`\`\`"
            echo ""
            echo "### Executive Summary"
            echo ""
            echo ""
            echo "### Vulnerability Analysis"
            echo ""
            echo ""
            echo "### Exploit Strategy"
            echo ""
            echo ""
            echo "### Implementation"
            echo ""
            echo ""
            echo "### Execution & Results"
            echo ""
            echo ""
        } > "$CHAL_README"

        green "    Wrote $CHAL_README"

        for F in "${C_FILES[@]}"; do
            [[ -z "$F" ]] && continue
            F_NAME=$(basename "$(echo "$F" | cut -d'?' -f1)")
            F_URL="${BASE_URL}${F}"
            bold "    Downloading $F_NAME..."
            curl -fsSL \
                -H "Authorization: Token ${TOKEN}" \
                "$F_URL" \
                --output "${CHAL_PATH}/${F_NAME}" \
                && green "    Saved ${CHAL_PATH}/${F_NAME}" \
                || yellow "    Failed to download $F_NAME"
        done
    done

    green "All challenges processed."
else
    if [[ "$USES_CTFD" == "y" || "$USES_CTFD" == "yes" ]]; then
        yellow "No token provided — skipping challenge fetch."
    fi
fi

echo ""
boldcyan "══════════════════════════════════════════════"
green "Setup complete for: $TITLE"
bold "  Folder: $(pwd)"
boldcyan "══════════════════════════════════════════════"
