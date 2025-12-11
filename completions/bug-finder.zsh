#compdef _bug_finder bug-finder
#
# zsh completion for bug-finder CLI
# Install with: bash scripts/install_completion.sh
#
# Provides intelligent tab-completion for bug-finder commands and options

_bug_finder() {
    local ret=1
    local -a state line expl
    local curcontext="$curcontext"

    # Main command completion
    local -a main_commands
    main_commands=(
        'scan:Scan a website for visual bugs similar to a provided example'
        'list-scans:List recent bug-finder scans and their status'
        'doctor:Check your environment setup for Bug Finder'
        'compare:Compare results between two scans'
        'export:Export bug scan results to various formats'
        'patterns:Manage custom bug patterns for scanning'
        'config-example:Generate an example configuration file'
    )

    _arguments -C \
        '(- *)--help[show help message]' \
        '(- *)--version[show version]' \
        '1: :->cmd' \
        '*::arg:->args' \
        && ret=0

    case "$state" in
        cmd)
            _describe 'commands' main_commands
            ret=0
            ;;
        args)
            case "$line[1]" in
                scan)
                    _bug_finder_scan
                    ret=0
                    ;;
                list-scans)
                    _bug_finder_list_scans
                    ret=0
                    ;;
                doctor)
                    _bug_finder_doctor
                    ret=0
                    ;;
                compare)
                    _bug_finder_compare
                    ret=0
                    ;;
                export)
                    _bug_finder_export
                    ret=0
                    ;;
                patterns)
                    _bug_finder_patterns
                    ret=0
                    ;;
                config-example)
                    _bug_finder_config_example
                    ret=0
                    ;;
            esac
            ;;
    esac

    return ret
}

_bug_finder_scan() {
    _arguments \
        '(-e --example-url)'{-e,--example-url}'[URL of a page showing the bug]:url:' \
        '(-s --site)'{-s,--site}'[Base URL of site to scan]:url:' \
        '(-m --max-pages)'{-m,--max-pages}'[Maximum number of pages to scan]:number:' \
        '(-b --bug-text)'{-b,--bug-text}'[Provide bug text directly]:text:' \
        '(-o --output)'{-o,--output}'[Output file path]:file:_files' \
        '(-f --format)'{-f,--format}'[Output format]:format:(txt csv html json all)' \
        '(-c --config)'{-c,--config}'[Configuration file]:file:_files' \
        '(-i --incremental)'{-i,--incremental}'[Enable incremental output]' \
        '(--pattern-file)--pattern-file[Load custom pattern from library]:pattern:' \
        '(--load-all-patterns)--load-all-patterns[Load all available patterns]' \
        '(-q --quiet)'{-q,--quiet}'[Minimal output]' \
        '(-v --verbose)'{-v,--verbose}'[Detailed debug output]' \
        '(--dry-run)--dry-run[Preview what scan would do without running]' \
        '(--help)-h[show help]' \
        '(--help)--help[show help]'
}

_bug_finder_list_scans() {
    _arguments \
        '(-l --limit)'{-l,--limit}'[Maximum number of scans to display]:number:' \
        '(-s --status)'{-s,--status}'[Filter by status]:status:(running completed completed_clean error)' \
        '(--help)-h[show help]' \
        '(--help)--help[show help]'
}

_bug_finder_doctor() {
    _arguments \
        '(--help)-h[show help]' \
        '(--help)--help[show help]'
}

_bug_finder_compare() {
    _arguments \
        '(-a --scan1)'{-a,--scan1}'[First scan ID to compare]:scan_id:' \
        '(-b --scan2)'{-b,--scan2}'[Second scan ID to compare]:scan_id:' \
        '(-f --file1)'{-f,--file1}'[Path to first results file]:file:_files' \
        '(-g --file2)'{-g,--file2}'[Path to second results file]:file:_files' \
        '(--help)-h[show help]' \
        '(--help)--help[show help]'
}

_bug_finder_export() {
    _arguments \
        '(-i --input)'{-i,--input}'[Path to JSON results file]:file:_files' \
        '(-f --format)'{-f,--format}'[Output format]:format:(markdown slack html)' \
        '(-o --output)'{-o,--output}'[Custom output path]:file:_files' \
        '(--help)-h[show help]' \
        '(--help)--help[show help]'
}

_bug_finder_patterns() {
    local -a patterns_commands
    patterns_commands=(
        'list:List all available patterns'
        'add:Create a new pattern interactively'
        'test:Test a pattern against content or URL'
        'template:Get a template for creating patterns'
    )

    _describe 'pattern commands' patterns_commands
}

_bug_finder_config_example() {
    _arguments \
        '(-o --output)'{-o,--output}'[Output path for config file]:file:_files' \
        '(--help)-h[show help]' \
        '(--help)--help[show help]'
}

# Call the main completion function
_bug_finder "$@"
