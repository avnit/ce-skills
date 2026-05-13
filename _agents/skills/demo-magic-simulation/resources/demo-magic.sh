#!/usr/bin/env bash

###############################################################################
# demo-magic.sh
#
# Embedded human simulation engine for bash presentation scripts.
# Simulates live typing character-by-character and pauses for interactive 
# presentation progression (ENTER key).
###############################################################################

# Global Configuration Defaults
TYPE_SPEED=${TYPE_SPEED:-20}
DEMO_PROMPT=${DEMO_PROMPT:-"$ "}

# Terminal Color Tokens
DEMO_CMD_COLOR=${DEMO_CMD_COLOR:-"\033[1;36m"}      # Bold Cyan
DEMO_COMMENT_COLOR=${DEMO_COMMENT_COLOR:-"\033[0;90m"} # Grey
COLOR_RESET="\033[0m"

##
# wait_for_enter: Pauses execution until the user presses ENTER.
##
function wait_for_enter() {
  read -rs
}

##
# simulate_typing: Types out a string character-by-character to the console.
##
function simulate_typing() {
  local text="$1"
  local color="$2"
  local len=${#text}
  
  # Compute sleep interval based on characters per second
  local delay=0.05
  if [[ "$TYPE_SPEED" -gt 0 ]]; then
    # Approximate standard speeds: 20 cps is 0.05s
    # Use simple precomputed boundaries to avoid external bc dependencies
    if [[ "$TYPE_SPEED" -ge 40 ]]; then delay=0.02
    elif [[ "$TYPE_SPEED" -ge 30 ]]; then delay=0.03
    elif [[ "$TYPE_SPEED" -ge 25 ]]; then delay=0.04
    elif [[ "$TYPE_SPEED" -ge 20 ]]; then delay=0.05
    elif [[ "$TYPE_SPEED" -ge 15 ]]; then delay=0.06
    elif [[ "$TYPE_SPEED" -ge 10 ]]; then delay=0.10
    else delay=0.15
    fi
  else
    delay=0
  fi

  for (( i=0; i<len; i++ )); do
    echo -ne "${color}${text:$i:1}${COLOR_RESET}"
    if [[ "$delay" != "0" ]]; then
      sleep "$delay"
    fi
  done
}

##
# pe: Print and Execute. Simulates typing out the command, waits for the user
#     to press ENTER, and then executes it live.
##
function pe() {
  local cmd="$1"
  echo -ne "${DEMO_PROMPT}"
  simulate_typing "$cmd" "${DEMO_CMD_COLOR}"
  wait_for_enter
  echo ""
  eval "$cmd"
  echo ""
}

##
# p: Print only. Simulates typing out the command but does not execute it.
##
function p() {
  local cmd="$1"
  echo -ne "${DEMO_PROMPT}"
  simulate_typing "$cmd" "${DEMO_COMMENT_COLOR}"
  wait_for_enter
  echo ""
}

##
# cmd: Execute immediately without visual typing simulation.
##
function cmd() {
  local cmd="$1"
  eval "$cmd"
  echo ""
}
