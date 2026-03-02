#!/usr/bin/env bash
# Bash completion script for pf task runner
# Install: source this file or copy to /etc/bash_completion.d/ or ~/.local/share/bash-completion/completions/pf

_pf_complete() {
    local cur prev words cword
    _init_completion || return

    # Common options that can appear anywhere
    local opts="env= hosts= host= user= port= sudo= sudo_user="
    
    # Built-in tasks
    local builtin_tasks="update upgrade install-base setup-venv reboot podman_install docker_compat nginx_install list help"
    
    # Get current word
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # If current word starts with a flag, complete with options
    if [[ "$cur" == *=* ]]; then
        # Already has =, don't complete further for most options
        return 0
    elif [[ "$cur" == env* ]] || [[ "$cur" == hosts* ]] || [[ "$cur" == host* ]] || \
         [[ "$cur" == user* ]] || [[ "$cur" == port* ]] || [[ "$cur" == sudo* ]] || \
         [[ "$cur" == sudo_user* ]]; then
        # Complete the option itself
        COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
        return 0
    fi

    # Check if we're completing a .pf file path
    if [[ "$cur" == *.pf* ]] || [[ "$prev" == "pf" && ! "$cur" == -* ]]; then
        # Complete .pf files
        COMPREPLY=( $(compgen -f -X '!*.pf' -- "$cur") )
        return 0
    fi

    # Try to get tasks from current Pfyfile.pf if it exists
    local pf_tasks=""
    if command -v pf &>/dev/null; then
        # Try to extract tasks, suppress errors
        pf_tasks=$(pf list 2>/dev/null | grep -E '^\s+[a-zA-Z]' | awk '{print $1}' | tr '\n' ' ')
    fi

    # Combine all available completions
    local all_completions="$builtin_tasks $pf_tasks $opts"
    
    # Filter completions based on current word
    COMPREPLY=( $(compgen -W "$all_completions" -- "$cur") )
    
    return 0
}

# Register the completion function
complete -F _pf_complete pf
