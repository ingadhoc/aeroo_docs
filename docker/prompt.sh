#!/bin/bash

#  SETUP CONSTANTS
#  Bunch-o-predefined colors.  Makes reading code easier than escape sequences.

# Various variables you might want for your PS1 prompt instead
PathShort="\w"
#PathFull="\W"
#NewLine="\n"
#Jobs="\j"
UserMachine="\u@\h $CONTAINER_NAME:"

# Reset
Color_Off="\[\033[0m\]"       # Text Reset
BICyan="\[\033[1;96m\]"       # Cyan
GREEN_WOE="\001\033[0;32m\002"
RED_WOE="\001\033[0;91m\002"

git_ps1_style(){
    # shellcheck disable=SC2155
    local git_branch="$(__git_ps1 2>/dev/null)";
    local git_ps1_style="";
    if [ -n "$git_branch" ]; then
        (git diff --quiet --ignore-submodules HEAD 2>/dev/null)
        local git_changed=$?
        if [ "$git_changed" == 0 ]; then
            git_ps1_style=$GREEN_WOE;
        else
            git_ps1_style=$RED_WOE;
        fi
        git_ps1_style=$git_ps1_style$git_branch
    fi
    echo -e "$git_ps1_style"
}
PS1=$BICyan$UserMachine$Color_Off$PathShort"\$(git_ps1_style)"$Color_Off\\n\$" "