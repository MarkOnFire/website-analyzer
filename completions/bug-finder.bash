# bash completion for bug-finder CLI
# Install with: bash scripts/install_completion.sh
#
# Provides intelligent tab-completion for bug-finder commands and options

_bug_finder_completion() {
    local cur prev words cword
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    words=("${COMP_WORDS[@]}")
    cword="${COMP_CWORD}"

    # Main commands
    local commands="scan list-scans doctor compare export patterns config-example"

    # Main options
    local main_options="--help -h --version"

    # Scan command options
    local scan_options="--example-url -e --site -s --max-pages -m --bug-text -b --output -o --format -f --config -c --incremental -i --pattern-file --load-all-patterns --quiet -q --verbose -v --dry-run --help"

    # List-scans options
    local list_scans_options="--limit -l --status -s --help"

    # Compare options
    local compare_options="--scan1 -a --scan2 -b --file1 -f --file2 -g --help"

    # Format options
    local formats="txt csv html json all markdown slack"

    # Status options
    local statuses="running completed completed_clean error"

    # Determine what kind of completion to provide
    case "${words[1]}" in
        scan)
            # Complete scan subcommand options and arguments
            case "$prev" in
                --example-url|-e|--site|-s|--bug-text|-b|--output|-o|--config|-c|--pattern-file)
                    # These take arguments - suggest nothing (shell will do file completion)
                    return 0
                    ;;
                --format|-f)
                    # Format options
                    COMPREPLY=($(compgen -W "$formats" -- "$cur"))
                    return 0
                    ;;
                --max-pages|-m)
                    # Number argument
                    return 0
                    ;;
                *)
                    # Complete options if current word starts with -
                    if [[ "$cur" == -* ]]; then
                        COMPREPLY=($(compgen -W "$scan_options" -- "$cur"))
                    fi
                    return 0
                    ;;
            esac
            ;;
        list-scans)
            # Complete list-scans options
            case "$prev" in
                --status|-s)
                    # Status options
                    COMPREPLY=($(compgen -W "$statuses" -- "$cur"))
                    return 0
                    ;;
                --limit|-l)
                    # Number argument
                    return 0
                    ;;
                *)
                    if [[ "$cur" == -* ]]; then
                        COMPREPLY=($(compgen -W "$list_scans_options" -- "$cur"))
                    fi
                    return 0
                    ;;
            esac
            ;;
        compare)
            # Complete compare options
            case "$prev" in
                --scan1|-a|--scan2|-b|--file1|-f|--file2|-g)
                    # These take arguments
                    return 0
                    ;;
                *)
                    if [[ "$cur" == -* ]]; then
                        COMPREPLY=($(compgen -W "$compare_options" -- "$cur"))
                    fi
                    return 0
                    ;;
            esac
            ;;
        doctor|export|patterns|config-example)
            # These commands have their own completion
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--help" -- "$cur"))
            fi
            return 0
            ;;
        *)
            # Complete main commands if first argument
            if [[ ${cword} -eq 1 ]]; then
                if [[ "$cur" == -* ]]; then
                    COMPREPLY=($(compgen -W "$main_options" -- "$cur"))
                else
                    COMPREPLY=($(compgen -W "$commands" -- "$cur"))
                fi
            fi
            return 0
            ;;
    esac
}

# Register completion for bug-finder command
complete -o bashdefault -o default -o nospace -F _bug_finder_completion bug-finder
complete -o bashdefault -o default -o nospace -F _bug_finder_completion python
