# Makefile for Practice Binaries
# Builds vulnerable binaries for debugging, exploitation, and fuzzing practice

CC = gcc
CFLAGS = -g -O0 -fno-stack-protector -z execstack -no-pie -Wno-format-security
LDFLAGS = -pthread

# Directories
BUFFER_DIR = buffer-overflow
FORMAT_DIR = format-string
HEAP_DIR = heap-exploits
INT_DIR = integer-overflow
RACE_DIR = race-condition
CMD_DIR = command-injection

# Buffer Overflow Binaries
BUFFER_BINS = \
	$(BUFFER_DIR)/stack_overflow \
	$(BUFFER_DIR)/heap_overflow

# Format String Binaries
FORMAT_BINS = \
	$(FORMAT_DIR)/format_vuln

# Heap Exploit Binaries
HEAP_BINS = \
	$(HEAP_DIR)/use_after_free \
	$(HEAP_DIR)/double_free

# Integer Overflow Binaries
INT_BINS = \
	$(INT_DIR)/int_overflow

# Race Condition Binaries
RACE_BINS = \
	$(RACE_DIR)/toctou_race

# Command Injection Binaries
CMD_BINS = \
	$(CMD_DIR)/cmd_injection

# All binaries
ALL_BINS = $(BUFFER_BINS) $(FORMAT_BINS) $(HEAP_BINS) $(INT_BINS) $(RACE_BINS) $(CMD_BINS)

# Default target
.PHONY: all
all: $(ALL_BINS)
	@echo ""
	@echo "✓ All practice binaries built successfully!"
	@echo ""
	@echo "Categories:"
	@echo "  - Buffer Overflow: $(BUFFER_BINS)"
	@echo "  - Format String: $(FORMAT_BINS)"
	@echo "  - Heap Exploits: $(HEAP_BINS)"
	@echo "  - Integer Overflow: $(INT_BINS)"
	@echo "  - Race Condition: $(RACE_BINS)"
	@echo "  - Command Injection: $(CMD_BINS)"
	@echo ""
	@echo "See README.md for usage instructions."
	@echo ""

# Buffer overflow targets
.PHONY: buffer-overflow
buffer-overflow: $(BUFFER_BINS)
	@echo "✓ Buffer overflow binaries built"

$(BUFFER_DIR)/stack_overflow: $(BUFFER_DIR)/stack_overflow.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

$(BUFFER_DIR)/heap_overflow: $(BUFFER_DIR)/heap_overflow.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

# Format string targets
.PHONY: format-string
format-string: $(FORMAT_BINS)
	@echo "✓ Format string binaries built"

$(FORMAT_DIR)/format_vuln: $(FORMAT_DIR)/format_vuln.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

# Heap exploit targets
.PHONY: heap-exploits
heap-exploits: $(HEAP_BINS)
	@echo "✓ Heap exploit binaries built"

$(HEAP_DIR)/use_after_free: $(HEAP_DIR)/use_after_free.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

$(HEAP_DIR)/double_free: $(HEAP_DIR)/double_free.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

# Integer overflow targets
.PHONY: integer-overflow
integer-overflow: $(INT_BINS)
	@echo "✓ Integer overflow binaries built"

$(INT_DIR)/int_overflow: $(INT_DIR)/int_overflow.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

# Race condition targets
.PHONY: race-condition
race-condition: $(RACE_BINS)
	@echo "✓ Race condition binaries built"

$(RACE_DIR)/toctou_race: $(RACE_DIR)/toctou_race.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

# Command injection targets
.PHONY: command-injection
command-injection: $(CMD_BINS)
	@echo "✓ Command injection binaries built"

$(CMD_DIR)/cmd_injection: $(CMD_DIR)/cmd_injection.c
	@echo "Building $@..."
	$(CC) $(CFLAGS) -o $@ $<

# Clean targets
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(ALL_BINS)
	rm -f $(BUFFER_DIR)/*.o $(FORMAT_DIR)/*.o $(HEAP_DIR)/*.o
	rm -f $(INT_DIR)/*.o $(RACE_DIR)/*.o $(CMD_DIR)/*.o
	@echo "✓ Clean complete"

# Test targets
.PHONY: test
test: all
	@echo ""
	@echo "=== Running Basic Tests ==="
	@echo ""
	@echo "Testing stack_overflow..."
	-$(BUFFER_DIR)/stack_overflow TEST 2>&1 | head -5
	@echo ""
	@echo "Testing heap_overflow..."
	-$(BUFFER_DIR)/heap_overflow TEST 2>&1 | head -5
	@echo ""
	@echo "Testing format_vuln..."
	-$(FORMAT_DIR)/format_vuln "test" 2>&1 | head -5
	@echo ""
	@echo "Testing use_after_free..."
	-$(HEAP_DIR)/use_after_free create TEST 2>&1 | head -5
	@echo ""
	@echo "Testing double_free..."
	-$(HEAP_DIR)/double_free create TEST 2>&1 | head -5
	@echo ""
	@echo "Testing int_overflow..."
	-$(INT_DIR)/int_overflow alloc 10 20 2>&1 | head -5
	@echo ""
	@echo "Testing toctou_race..."
	-$(RACE_DIR)/toctou_race setup 2>&1 | head -5
	@echo ""
	@echo "Testing cmd_injection..."
	-$(CMD_DIR)/cmd_injection setup 2>&1 | head -5
	@echo ""
	@echo "✓ All tests complete"

# Help target
.PHONY: help
help:
	@echo "Practice Binaries Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all              - Build all binaries (default)"
	@echo "  buffer-overflow  - Build buffer overflow binaries"
	@echo "  format-string    - Build format string binaries"
	@echo "  heap-exploits    - Build heap exploit binaries"
	@echo "  integer-overflow - Build integer overflow binaries"
	@echo "  race-condition   - Build race condition binaries"
	@echo "  command-injection- Build command injection binaries"
	@echo "  test             - Run basic tests on all binaries"
	@echo "  clean            - Remove all built binaries"
	@echo "  help             - Show this help message"
	@echo ""
	@echo "Compilation flags:"
	@echo "  -g                   Debug symbols"
	@echo "  -O0                  No optimization"
	@echo "  -fno-stack-protector No stack canaries"
	@echo "  -z execstack         Executable stack"
	@echo "  -no-pie              No position independent code"
	@echo ""
	@echo "See README.md for detailed usage instructions."

.PHONY: info
info:
	@echo "Practice Binaries Information"
	@echo ""
	@echo "Buffer Overflow:"
	@for bin in $(BUFFER_BINS); do \
		if [ -f $$bin ]; then \
			echo "  ✓ $$bin"; \
			file $$bin | sed 's/^/    /'; \
		else \
			echo "  ✗ $$bin (not built)"; \
		fi; \
	done
	@echo ""
	@echo "Format String:"
	@for bin in $(FORMAT_BINS); do \
		if [ -f $$bin ]; then \
			echo "  ✓ $$bin"; \
			file $$bin | sed 's/^/    /'; \
		else \
			echo "  ✗ $$bin (not built)"; \
		fi; \
	done
	@echo ""
	@echo "Heap Exploits:"
	@for bin in $(HEAP_BINS); do \
		if [ -f $$bin ]; then \
			echo "  ✓ $$bin"; \
			file $$bin | sed 's/^/    /'; \
		else \
			echo "  ✗ $$bin (not built)"; \
		fi; \
	done
	@echo ""
	@echo "Integer Overflow:"
	@for bin in $(INT_BINS); do \
		if [ -f $$bin ]; then \
			echo "  ✓ $$bin"; \
			file $$bin | sed 's/^/    /'; \
		else \
			echo "  ✗ $$bin (not built)"; \
		fi; \
	done
	@echo ""
	@echo "Race Condition:"
	@for bin in $(RACE_BINS); do \
		if [ -f $$bin ]; then \
			echo "  ✓ $$bin"; \
			file $$bin | sed 's/^/    /'; \
		else \
			echo "  ✗ $$bin (not built)"; \
		fi; \
	done
	@echo ""
	@echo "Command Injection:"
	@for bin in $(CMD_BINS); do \
		if [ -f $$bin ]; then \
			echo "  ✓ $$bin"; \
			file $$bin | sed 's/^/    /'; \
		else \
			echo "  ✗ $$bin (not built)"; \
		fi; \
	done
