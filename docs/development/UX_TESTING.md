# Bug Finder UX Improvements - Testing Guide

## Testing Scenarios

### 1. Standard Mode Testing

**Command:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail" \
  --site "https://www.example.com" \
  --max-pages 50 \
  --bug-text '[[{"fid":"test","view_mode":"full"}]]'
```

**Expected Output:**
- Header panel showing scan configuration
- Real-time progress bar with URL, percentage, elapsed/remaining time
- Green checkmarks when bugs are found
- Summary table with scan statistics
- List of top affected pages
- Final confirmation message

**Verification Points:**
- [ ] Progress bar updates smoothly
- [ ] Current URL is displayed (truncated if long)
- [ ] Percentage and time estimates are accurate
- [ ] Bug found notifications appear
- [ ] Summary shows correct statistics
- [ ] Output is readable and professional

---

### 2. Quiet Mode Testing

**Command:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../page" \
  --site "https://www.example.com" \
  --max-pages 50 \
  --bug-text '[[{"fid":"test","view_mode":"full"}]]' \
  --quiet
```

**Expected Output:**
- Minimal console output
- No progress bar
- No intermediate status messages
- Only critical errors and final results
- JSON file saved silently

**Verification Points:**
- [ ] No progress bar is displayed
- [ ] No "Scanning..." or configuration messages
- [ ] Only final summary shown (if results found)
- [ ] Still shows file save location
- [ ] Errors are still displayed
- [ ] Good for piping to logs or CI/CD

---

### 3. Verbose Mode Testing

**Command:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../page" \
  --site "https://www.example.com" \
  --max-pages 10 \
  --bug-text '[[{"fid":"test","view_mode":"full"}]]' \
  --verbose
```

**Expected Output:**
- All standard mode output
- Plus detailed error messages for failed URLs
- Additional debug information
- Pattern matching details
- Enhanced logging output

**Verification Points:**
- [ ] Shows all standard mode information
- [ ] Error messages include more detail
- [ ] Failed URL reasons are explained
- [ ] Debug information is helpful for troubleshooting
- [ ] Not overwhelming with data

---

### 4. Incremental Mode Testing

**Command:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../page" \
  --site "https://www.example.com" \
  --max-pages 200 \
  --bug-text '[[{"fid":"test","view_mode":"full"}]]' \
  --incremental
```

**Expected Output:**
- Standard progress bar
- Periodic "Saving progress" messages
- `.partial.json` file created in project directory
- On completion: renamed to final filename

**Verification Points:**
- [ ] `.partial.json` file appears during scan
- [ ] File is valid JSON
- [ ] File contains progress metadata
- [ ] File updates as bugs are found
- [ ] File is renamed to final name on completion
- [ ] Partial results usable if interrupted

**Test Interruption (Ctrl+C):**
- [ ] Progress saves to .partial.json before exit
- [ ] File is valid JSON
- [ ] No data loss
- [ ] Clean exit message

---

### 5. Combined Flags Testing

**Command:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/.../page" \
  --site "https://www.example.com" \
  --max-pages 100 \
  --bug-text '[[{"fid":"test","view_mode":"full"}]]' \
  --incremental \
  --verbose
```

**Expected Output:**
- Standard and verbose output
- Progress bar with real-time updates
- Detailed error messages
- Incremental saves with progress messages

**Verification Points:**
- [ ] All three features work together
- [ ] No conflicting output
- [ ] Progress and incremental saves work
- [ ] Verbose details don't interfere with progress bar

---

### 6. Error Handling Testing

**Scenario A: Invalid URL**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "not-a-url" \
  --site "https://www.example.com" \
  --max-pages 10
```

**Expected:** Error message displayed

**Scenario B: Network Error**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://does-not-exist-12345.com" \
  --site "https://www.example.com" \
  --max-pages 10
```

**Expected:**
- Progress continues
- Error logged (verbose mode shows details)
- Final count includes failed URLs

**Scenario C: Timeout (Standard)**
```bash
# Site doesn't respond within timeout
```

**Expected:**
- Error is logged
- Scan continues with next pages
- Final report shows failures

**Verification Points:**
- [ ] Errors don't crash the scanner
- [ ] Progress bar continues
- [ ] Quiet mode silences errors appropriately
- [ ] Verbose mode shows full error details
- [ ] Failed URLs are counted in summary

---

## Performance Testing

### Test Case: Large Scan
**Command:**
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/..." \
  --site "https://www.wpr.org" \
  --max-pages 1000 \
  --incremental \
  --verbose
```

**Metrics to Track:**
- [ ] Progress bar updates smoothly (no lag)
- [ ] Memory usage stays reasonable
- [ ] File I/O (incremental saves) doesn't block
- [ ] Scan rate displayed is accurate
- [ ] Time estimates are reasonable

**Verification Points:**
- [ ] No memory leaks over long scans
- [ ] Console output is responsive
- [ ] Incremental saves don't cause slowdown
- [ ] Final statistics are correct

---

## Output Format Verification

### Check Standard Output
- [ ] Colors are visible (green, red, cyan, yellow)
- [ ] Progress bar renders correctly
- [ ] Tables are aligned
- [ ] Panels display properly
- [ ] Unicode characters (✓, ✗) work

### Check Quiet Output
- [ ] Very minimal text
- [ ] Only critical info
- [ ] Suitable for logs
- [ ] Exit codes correct (0=success, 1=error)

### Check Verbose Output
- [ ] All debug info present
- [ ] Error details helpful
- [ ] Not overwhelming
- [ ] Structure is clear

---

## Integration Testing

### With Configuration Files
```bash
python -m src.analyzer.cli bug-finder scan \
  --config bug-finder-config.json \
  --site "https://www.example.com" \
  --quiet
```

**Expected:**
- [ ] Config loads correctly
- [ ] Quiet flag overrides verbose config
- [ ] Max pages from config used if not overridden

### With Export Formats
```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "..." \
  --site "https://www.example.com" \
  --max-pages 50 \
  --format all
```

**Expected:**
- [ ] Progress shows during scan
- [ ] All export formats created
- [ ] Files are valid
- [ ] Final message lists all files

---

## Edge Cases

### Test: Very Long URL
**Command with long URL (>100 chars)**

**Expected:**
- [ ] URL truncated in progress bar (shows "...at end")
- [ ] Full URL in results
- [ ] No display corruption

### Test: No Bugs Found
**Scan where no patterns match**

**Expected:**
- [ ] Progress bar completes 100%
- [ ] Summary shows 0 bugs found
- [ ] Still shows scan statistics
- [ ] No false positives

### Test: All Pages Fail
**Unreachable site**

**Expected:**
- [ ] Errors are recorded
- [ ] Final summary shows failures
- [ ] Scanner doesn't crash
- [ ] User can see what happened

### Test: Immediate Interruption
**Press Ctrl+C immediately after start**

**Expected:**
- [ ] Graceful exit
- [ ] Partial results saved (if incremental)
- [ ] No corrupted files
- [ ] Clean error message

---

## Checklist for Release

- [ ] All syntax valid (py_compile passes)
- [ ] Rich library imports work
- [ ] Standard mode displays correctly
- [ ] Quiet mode works as expected
- [ ] Verbose mode shows debug info
- [ ] Incremental mode saves progress
- [ ] Combined modes work together
- [ ] Error handling is robust
- [ ] Progress bar is smooth
- [ ] Summary statistics are accurate
- [ ] Colors display correctly
- [ ] No performance degradation
- [ ] Documentation is complete
- [ ] Example output is accurate

---

## Manual Testing Script

```bash
#!/bin/bash
# Quick test of all modes

echo "=== Testing Standard Mode ==="
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/..." \
  --site "https://www.example.com" \
  --max-pages 10 \
  --bug-text '[[{"fid":"test"}]]'

echo -e "\n=== Testing Quiet Mode ==="
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/..." \
  --site "https://www.example.com" \
  --max-pages 10 \
  --bug-text '[[{"fid":"test"}]]' \
  --quiet

echo -e "\n=== Testing Verbose Mode ==="
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/..." \
  --site "https://www.example.com" \
  --max-pages 5 \
  --bug-text '[[{"fid":"test"}]]' \
  --verbose

echo -e "\n=== All tests complete ==="
```
