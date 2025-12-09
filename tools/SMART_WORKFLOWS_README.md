# Smart Workflows and Tool Integration

## Current Implementation Status

This directory contains the smart workflow and tool integration system for pf-runner. The implementation combines features from multiple PRs (#193, #194, #195, #196) into a unified system.

### ⚠️ Implementation Notice

**Current Status:** Stub/Minimal Implementation

The tools in this directory are currently **functional stubs** that provide:
- ✅ Basic command-line interface
- ✅ Proper argument parsing
- ✅ Helpful output messages
- ✅ Integration with pf task system
- ⚠️ Placeholder analysis logic (not production-ready)

**Why Stubs?**
- Allows testing of workflow orchestration without implementing complex analysis algorithms
- Provides working CLI interface for users to understand the system
- Enables gradual enhancement without breaking existing functionality
- Permits immediate integration into pf task system

### Directory Structure

```
tools/
├── orchestration/           # Workflow coordination and management
│   ├── tool-detector.mjs   # Tool capability detection (stub)
│   ├── workflow-engine.mjs # Workflow orchestration (stub)
│   ├── smart_analyzer.py   # Binary analysis (stub)
│   ├── smart_exploiter.py  # Exploit development (stub)
│   └── workflow_manager.py # Workflow state management (stub)
│
├── unified/                 # Unified tool interfaces
│   └── unified_checksec.py # Consolidated checksec (stub)
│
└── smart-workflows/         # Smart workflow implementations
    ├── target_detector.py   # Target type detection (functional)
    ├── smart_scanner.py     # Adaptive scanning (stub)
    └── smart_fuzzer_selector.py # Fuzzer selection (stub)
```

### Functional vs. Stub Status

**Functional (Production-Ready):**
- `target_detector.py` - Basic target type detection works
- CLI argument parsing across all tools
- Integration with pf tasks
- Help messages and user guidance

**Stub (Needs Implementation):**
- `unified_checksec.py` - Returns hardcoded "Unknown" values
- `smart_analyzer.py` - Only prints messages, no actual analysis
- `smart_exploiter.py` - Placeholder exploit generation
- `workflow-engine.mjs` - Logs parameters but doesn't execute workflows
- `tool-detector.mjs` - Placeholder tool detection
- `smart_scanner.py` - Basic output only
- `smart_fuzzer_selector.py` - No actual fuzzing

### Using the Smart Workflows

**What Works Now:**
```bash
# These commands work and provide useful output:
pf smart-help                     # Shows comprehensive help
pf smart-detect target=/bin/ls    # Detects target type
pf autopwn binary=./target        # Runs workflow (with stubs)
pf autoweb url=http://example.com # Runs workflow (with stubs)
```

**What to Expect:**
- Tasks execute without errors
- Helpful messages guide users
- Stub tools print what they would do
- No actual security analysis yet

### Enhancement Roadmap

**Phase 1: Current (Stubs)**
- ✅ CLI interfaces
- ✅ Task integration
- ✅ Help system
- ✅ Basic target detection

**Phase 2: Core Features (Next)**
- [ ] Implement unified_checksec with real security analysis
- [ ] Add actual binary analysis in smart_analyzer
- [ ] Implement tool detection logic
- [ ] Add workflow state management

**Phase 3: Advanced Features**
- [ ] Implement exploit generation
- [ ] Add fuzzing integration
- [ ] Create workflow orchestration engine
- [ ] Add machine learning for tool selection

### Contributing Enhancements

To enhance any stub implementation:

1. **Keep backward compatibility** - Maintain existing CLI arguments
2. **Add real functionality** - Replace `print()` with actual analysis
3. **Handle errors gracefully** - Don't break if tools are missing
4. **Add tests** - Verify functionality works as expected
5. **Update this README** - Move from "Stub" to "Functional" status

### Example Enhancement

To enhance `unified_checksec.py`:

```python
# Current (stub):
result = {
    'relro': 'Unknown',
    'canary': 'Unknown'
}

# Enhanced (functional):
import subprocess
result = {
    'relro': detect_relro(binary_path),
    'canary': detect_canary(binary_path)
}
```

### Tool Dependencies

**Required for Full Functionality:**
- `checksec` - Binary security feature detection
- `gdb` or `lldb` - Debugging and analysis
- `radare2` - Reverse engineering
- `ROPgadget` - ROP chain finding
- `pwntools` - Exploit development
- `node` - JavaScript tool execution

**Current Graceful Degradation:**
- Missing tools don't cause failures
- Stub implementations work without dependencies
- Users get helpful "not implemented yet" messages

### Questions?

See the main project documentation:
- `COMBINED_PRS_SUMMARY.md` - How this system was created
- `README.md` - Overall project documentation
- `CONTRIBUTING.md` - How to contribute enhancements

### License

Same as parent project (MIT License)
