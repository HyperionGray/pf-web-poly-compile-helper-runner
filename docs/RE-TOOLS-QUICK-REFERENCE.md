# RE/Debugging/Exploit Tools - Quick Reference

Quick lookup table for missing tools. See [MISSING-RE-DEBUG-EXPLOIT-TOOLS.md](MISSING-RE-DEBUG-EXPLOIT-TOOLS.md) for detailed descriptions.

## 🔥 High Priority (Must Have)

| Tool | Category | Primary Use Case | Platform |
|------|----------|------------------|----------|
| **Frida** | Dynamic Analysis | Runtime instrumentation & hooking (mobile + desktop) | All |
| **pwntools** | Exploit Dev | Exploit development, ROP chains, shellcode | Linux |
| **AFL++** | Fuzzing | Coverage-guided fuzzing | Linux/macOS |
| **ROPgadget/ropper** | Exploit Dev | ROP gadget finding & chain building | All |
| **IDA Pro/Free** | Static Analysis | Industry-standard disassembler/decompiler | All |
| **Intel Pin** | Dynamic Analysis | Instruction-level instrumentation | All |
| **Angr** | Symbolic Execution | Automated vulnerability discovery | All |
| **checksec** | Security Analysis | Binary protection identification | Linux |
| **libFuzzer** | Fuzzing | LLVM in-process fuzzing | All |

## 🟡 Medium Priority (Nice to Have)

| Tool | Category | Primary Use Case | Platform |
|------|----------|------------------|----------|
| **Unicorn Engine** | Emulation | CPU emulation for shellcode/unpacking | All |
| **Valgrind** | Memory Analysis | Memory leak & corruption detection | Linux |
| **LIEF** | Binary Modification | Advanced binary patching | All |
| **DynamoRIO** | Dynamic Analysis | Open-source binary instrumentation | All |
| **Hopper** | Static Analysis | macOS/Linux disassembler | macOS/Linux |
| **qiling** | Emulation | High-level binary emulation | All |
| **Honggfuzz** | Fuzzing | Hardware-assisted fuzzing | Linux |
| **Metasploit** | Exploit Framework | Payload generation & exploitation | All |
| **Wireshark/tshark** | Network Analysis | Protocol analysis & traffic capture | All |
| **APKTool/jadx** | Mobile (Android) | APK decompilation & analysis | All |
| **exploitable** | Crash Analysis | GDB plugin for crash triaging | Linux |
| **strace/ltrace** | System Tracing | System/library call tracing (better integration) | Linux |
| **E9Patch** | Binary Rewriting | Static binary instrumentation | Linux |

## 🟢 Low Priority (Advanced/Niche)

| Tool | Category | Primary Use Case | Platform |
|------|----------|------------------|----------|
| **Binary Ninja API** | Static Analysis | Automated analysis scripting | All |
| **Cutter** | Static Analysis | radare2 GUI (already have r2) | All |
| **QEMU instrumentation** | Emulation | Cross-architecture analysis | All |
| **class-dump** | Mobile (iOS) | iOS binary analysis | macOS |
| **Dyninst** | Binary Modification | Runtime binary modification | Linux |
| **BinDiff/Diaphora** | Binary Comparison | Patch & version diffing | All |
| **YARA** | Pattern Matching | Malware identification | All |
| **Capstone/Keystone** | Assembly Tools | Programmatic asm/disasm | All |
| **findcrypt** | Crypto Analysis | Crypto constant identification | All |
| **hashcat/John** | Password Cracking | Hash cracking | All |
| **unipacker/upx** | Unpacking | Packed binary unpacking | All |

## 📋 Quick Integration Checklist

When adding a new tool, ensure:

- [ ] Installation task (`pf install-TOOL`)
- [ ] Basic usage tasks (`pf TOOL-analyze`, etc.)
- [ ] Help/reference task (`pf TOOL-help`)
- [ ] Integration with existing workflows
- [ ] Documentation in main README
- [ ] Example workflow or demo
- [ ] Cross-platform support (where applicable)
- [ ] Error handling and validation

## 🚀 Suggested Implementation Order

### Week 1-2: Core Exploit Dev
1. pwntools
2. ROPgadget
3. checksec

### Week 3-4: Advanced Fuzzing
1. AFL++
2. libFuzzer integration

### Week 5-6: Dynamic Analysis
1. Frida
2. Intel Pin

### Week 7-8: Advanced Static Analysis
1. IDA Free integration
2. Angr

### Week 9-10: Emulation & Utilities
1. Unicorn Engine
2. Valgrind
3. LIEF

## 🔗 Cross-Tool Workflows

### Workflow 1: Complete Binary Analysis
```bash
pf checksec binary=target          # Check protections
pf ida-analyze binary=target       # Static analysis
pf frida-trace binary=target       # Dynamic trace
pf angr-symbolic-exec binary=target # Symbolic execution
```

### Workflow 2: Exploit Development
```bash
pf checksec binary=target              # Check protections
pf rop-find-gadgets binary=target     # Find ROP gadgets
pf pwn-template output=exploit.py     # Generate template
pf pwn-rop binary=target output=rop.py # Build ROP chain
```

### Workflow 3: Fuzzing Campaign
```bash
pf afl-instrument source=target.c       # Instrument
pf afl-fuzz binary=target input=corpus  # Fuzz
pf afl-triage-crashes crashes=out/     # Triage
pf exploitable crashes=out/crashes/    # Assess exploitability
```

### Workflow 4: Mobile App Analysis
```bash
pf apk-decompile apk=app.apk         # Decompile
pf apk-analyze apk=app.apk           # Static analysis
pf frida-hook binary=app.apk         # Dynamic analysis
```

## 📖 Related Documentation

- [Detailed Tool List](MISSING-RE-DEBUG-EXPLOIT-TOOLS.md) - Full descriptions and integration suggestions
- [Kernel Debugging Guide](KERNEL-DEBUGGING.md) - Existing kernel debugging features
- [Binary Injection Guide](BINARY-INJECTION.md) - Current injection capabilities
- [LLVM Lifting Guide](LLVM-LIFTING.md) - Binary lifting documentation

## 🤝 Community Contributions

Have suggestions for tools we missed? 

1. Fork the repository
2. Add tool to appropriate section
3. Include description and integration suggestions
4. Submit PR with rationale

## 📊 Tool Comparison Charts

### Static Analysis Tools

| Feature | IDA Pro | Ghidra ✓ | Binary Ninja | radare2 ✓ |
|---------|---------|----------|--------------|-----------|
| Disassembly | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Decompilation | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Scripting | Python | Python/Java | Python | Python/JS |
| Cost | $$$$ | Free | $$$ | Free |
| Learning Curve | Medium | Medium | Easy | Hard |

✓ = Currently integrated

### Dynamic Analysis Tools

| Feature | Frida | Pin | DynamoRIO | LLDB ✓ | GDB ✓ |
|---------|-------|-----|-----------|---------|--------|
| Runtime Hooking | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Mobile Support | ⭐⭐⭐⭐⭐ | ❌ | ❌ | ⭐⭐⭐ | ⭐⭐⭐ |
| Performance | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Multi-platform | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

✓ = Currently integrated

### Fuzzers

| Feature | AFL++ | libFuzzer | Syzkaller ✓ | Honggfuzz |
|---------|-------|-----------|-------------|-----------|
| Coverage-guided | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Speed | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| User-space | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ |
| Kernel-space | ⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Setup Ease | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |

✓ = Currently integrated

---

*For detailed tool descriptions, integration suggestions, and implementation phases, see [MISSING-RE-DEBUG-EXPLOIT-TOOLS.md](MISSING-RE-DEBUG-EXPLOIT-TOOLS.md)*
