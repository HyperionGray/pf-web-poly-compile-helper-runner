# Smart Workflows and Tool Integration

## Current Implementation Status

This directory contains the smart workflow and tool integration system for pf-runner. The implementation combines features from multiple PRs (#193, #194, #195, #196) into a unified system.

### ✅ Implementation Status - Functional!

**Current Status:** Core functionality is now implemented and working!

The tools in this directory now provide:
- ✅ Working command-line interfaces
- ✅ Proper argument parsing
- ✅ Real analysis and detection functionality
- ✅ Integration with pf task system
- ✅ Production-ready core features

**What Changed?**
- Stub implementations have been replaced with real functionality
- Tools now perform actual security analysis and tool detection
- Integrated with existing security and analysis modules
- Added comprehensive error handling

### Directory Structure

```
tools/
├── orchestration/           # Workflow coordination and management
│   ├── tool-detector.mjs   # Tool capability detection (✅ FUNCTIONAL)
│   ├── workflow-engine.mjs # Workflow orchestration (stub)
│   ├── smart_analyzer.py   # Binary analysis (✅ FUNCTIONAL)
│   ├── smart_exploiter.py  # Exploit workflow planner (✅ FUNCTIONAL)
│   └── workflow_manager.py # Workflow state management (stub)
│
├── unified/                 # Unified tool interfaces
│   └── unified_checksec.py # Consolidated checksec (✅ FUNCTIONAL)
│
├── security/                # Security analysis tools
│   └── checksec.py         # Pure Python checksec implementation (✅ FUNCTIONAL)
│
└── smart-workflows/         # Smart workflow implementations
    ├── target_detector.py   # Target type detection (functional)
    ├── smart_scanner.py     # Adaptive scanning (stub)
    └── smart_fuzzer_selector.py # Fuzzer selection (stub)
```

### Functional Status

**✅ Production-Ready (Fully Functional):**
- `unified_checksec.py` - Real binary security analysis with risk scoring
  - Detects RELRO, stack canary, NX, PIE, RPATH, FORTIFY_SOURCE
  - Calculates risk scores (0-100)
  - Supports JSON and text output with emoji indicators
- `smart_analyzer.py` - Comprehensive binary analysis
  - Basic analysis: file type, security features, interesting strings, dependencies
  - Deep analysis: symbol/section/function analysis
  - Integrates with unified_checksec
- `tool-detector.mjs` - Actual tool detection
  - Detects 17 security tools across 7 categories
  - Returns real availability status
  - Supports table and JSON output
- `smart_exploiter.py` - Exploit workflow planning and template generation
  - Analyzes target hardening features and recommends techniques
  - Generates exploit templates via pwntools (with robust fallback template)
  - Supports focused technique-first workflows (e.g. rop_chain, ret2libc)
- `target_detector.py` - Basic target type detection
- `checksec.py` - Pure Python implementation with real ELF analysis

**⚠️ Stub (Needs Implementation):**
- `workflow-engine.mjs` - Logs parameters but doesn't execute workflows
- `workflow_manager.py` - No state management yet
- `smart_scanner.py` - Basic output only
- `smart_fuzzer_selector.py` - No actual fuzzing

### Using the Smart Workflows

**What Works Now:**
```bash
# These commands are fully functional:
pf smart-detect target=/bin/ls           # Detects target type
pf unified-checksec binary=/bin/ls       # Real security analysis with risk scoring
pf smart-analyze target=/bin/ls          # Comprehensive binary analysis
pf smart-analyze target=/bin/ls --deep-analysis  # Deep analysis with symbols/sections
pf smart-exploit target=/bin/ls          # Build exploit workflow + template
pf smart-detect-tools                    # Detect installed security tools
pf autopwn binary=./target               # Works with real security analysis
pf autoweb url=http://example.com        # Works with real web scanning

# Tool detection:
pf smart-detect-tools                    # Table format
pf smart-detect-tools --format json      # JSON format
```

**What to Expect:**
- **unified-checksec**: Full security feature analysis, risk scoring, colored output
- **smart-analyze**: Real binary analysis with multiple checks
- **smart-exploit**: Practical exploit plan + starter template output
- **tool-detector**: Actual detection of installed tools
- **autopwn/autoweb**: Now use real security analysis in Phase 1

**Example Output:**
```
🔍 Unified Security Analysis: ls
============================================================

Security Features:
  ✅ RELRO:          Full RELRO
  ✅ Stack Canary:   Yes
  ✅ NX (DEP):       Yes
  ✅ PIE (ASLR):     PIE enabled
  ✅ RPATH:          No
  ✅ FORTIFY:        Yes

📊 Risk Assessment:
  Risk Score:     0/100
  Status:         Secure
```

### Enhancement Roadmap

**Phase 1: Core Features (✅ COMPLETE)**
- ✅ unified_checksec with real security analysis
- ✅ smart_analyzer with actual binary analysis
- ✅ tool-detector with real tool detection
- ✅ Risk scoring and assessment

**Phase 2: Integration (Current)**
- ✅ Updated autopwn to use unified-checksec
- ✅ Updated smart-exploit-chain to use unified-checksec
- [ ] Test all workflows end-to-end
- [ ] Add integration tests

**Phase 3: Advanced Features (Next)**
- [ ] Add workflow state management
- [ ] Create workflow orchestration engine
- [ ] Add machine learning for tool selection

### Tool Consolidation

**Checksec Implementations (Reduced Redundancy):**
1. `tools/security/checksec.py` - Core implementation (pure Python, ELF analysis)
2. `tools/unified/unified_checksec.py` - Unified interface (uses #1, adds risk scoring)
3. `tools/exploit/checksec_batch.py` - Batch processing (wraps external checksec tool)

**Recommended Usage:**
- Single binary: `pf unified-checksec binary=/path/to/file`
- Batch analysis: `pf checksec-batch dir=/path/to/dir`
- JSON output: `pf unified-checksec binary=/path/to/file --json`

### Contributing Enhancements

To enhance any stub implementation:

1. **Keep backward compatibility** - Maintain existing CLI arguments
2. **Add real functionality** - Replace `print()` with actual analysis
3. **Handle errors gracefully** - Don't break if tools are missing
4. **Add tests** - Verify functionality works as expected
5. **Update this README** - Move from "Stub" to "Functional" status

### Tool Dependencies

**Required for Full Functionality:**
- `readelf`, `nm`, `objdump`, `strings`, `ldd` - Binary analysis (usually installed)
- `file` - File type detection (usually installed)
- `checksec` - External checksec tool (optional, we have Python implementation)
- `gdb` or `lldb` - Debugging and analysis
- `radare2` - Reverse engineering
- `ROPgadget` - ROP chain finding
- `pwntools` - Exploit development
- `node` - JavaScript tool execution

**Tool Detection:**
Use `pf smart-detect-tools` to see what's installed and what's missing.

**Current Graceful Degradation:**
- Core tools (readelf, objdump, nm, file, strings) work out of the box on most systems
- Missing advanced tools don't cause failures
- Users get helpful error messages when tools are unavailable

### Questions?

See the main project documentation:
- `docs/reviews/COMBINED_PRS_SUMMARY.md` - How this system was created
- `README.md` - Overall project documentation
- `docs/development/CONTRIBUTING.md` - How to contribute enhancements

### License

Same as parent project (MIT License)
