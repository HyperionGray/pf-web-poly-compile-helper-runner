# Makefile for Heap Spray Helpers and Demos
# FOR EDUCATIONAL PURPOSES ONLY

CC := gcc
CFLAGS := -Wall -Wextra -O2 -std=c99
LDFLAGS := -lm

# Detect platform
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
    CFLAGS += -D__LINUX__
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
    CFLAGS += -D__MACOS__
endif

# Directories
SRC_DIR := src
EXAMPLES_DIR := examples
TOOLS_DIR := tools
BUILD_DIR := build
OBJ_DIR := $(BUILD_DIR)/obj

# Source files
LIB_SRC := $(SRC_DIR)/heap_spray.c
LIB_OBJ := $(OBJ_DIR)/heap_spray.o
LIB_HEADER := $(SRC_DIR)/heap_spray.h

EXAMPLE_SRCS := $(wildcard $(EXAMPLES_DIR)/*.c)
TOOL_SRCS := $(wildcard $(TOOLS_DIR)/*.c)

# Targets
EXAMPLE_BINS := $(patsubst $(EXAMPLES_DIR)/%.c,$(BUILD_DIR)/%,$(EXAMPLE_SRCS))
TOOL_BINS := $(patsubst $(TOOLS_DIR)/%.c,$(BUILD_DIR)/%,$(TOOL_SRCS))

ALL_BINS := $(EXAMPLE_BINS) $(TOOL_BINS)

# Default target
.PHONY: all
all: $(BUILD_DIR) $(OBJ_DIR) $(LIB_OBJ) $(ALL_BINS)
	@echo "✓ Build complete for platform: $(PLATFORM)"
	@echo "✓ Binaries available in $(BUILD_DIR)/"
	@echo ""
	@echo "Run demos with:"
	@echo "  ./$(BUILD_DIR)/basic_demo"
	@echo "  ./$(BUILD_DIR)/vulnerability_demo"
	@echo "  ./$(BUILD_DIR)/heap_analyzer"

# Create directories
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(OBJ_DIR):
	@mkdir -p $(OBJ_DIR)

# Build library object
$(LIB_OBJ): $(LIB_SRC) $(LIB_HEADER) | $(OBJ_DIR)
	@echo "Compiling heap spray library..."
	$(CC) $(CFLAGS) -c $< -o $@

# Build examples
$(BUILD_DIR)/%: $(EXAMPLES_DIR)/%.c $(LIB_OBJ) | $(BUILD_DIR)
	@echo "Building example: $@"
	$(CC) $(CFLAGS) $< $(LIB_OBJ) $(LDFLAGS) -o $@

# Build tools
$(BUILD_DIR)/%: $(TOOLS_DIR)/%.c $(LIB_OBJ) | $(BUILD_DIR)
	@echo "Building tool: $@"
	$(CC) $(CFLAGS) $< $(LIB_OBJ) $(LDFLAGS) -o $@

# Individual targets
.PHONY: basic_demo
basic_demo: $(BUILD_DIR)/basic_demo

.PHONY: vulnerability_demo
vulnerability_demo: $(BUILD_DIR)/vulnerability_demo

.PHONY: heap_analyzer
heap_analyzer: $(BUILD_DIR)/heap_analyzer

# Run targets
.PHONY: run-basic
run-basic: $(BUILD_DIR)/basic_demo
	@echo "Running basic demo..."
	@./$(BUILD_DIR)/basic_demo

.PHONY: run-vulns
run-vulns: $(BUILD_DIR)/vulnerability_demo
	@echo "Running vulnerability demo..."
	@./$(BUILD_DIR)/vulnerability_demo

.PHONY: run-analyzer
run-analyzer: $(BUILD_DIR)/heap_analyzer
	@echo "Running heap analyzer..."
	@./$(BUILD_DIR)/heap_analyzer

.PHONY: run-all
run-all: run-basic run-vulns run-analyzer

# Clean
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@echo "✓ Clean complete"

# Help
.PHONY: help
help:
	@echo "Heap Spray Helpers and Demos - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all             - Build all demos and tools (default)"
	@echo "  basic_demo      - Build basic heap spray demo"
	@echo "  vulnerability_demo - Build vulnerability demo"
	@echo "  heap_analyzer   - Build heap analysis tool"
	@echo ""
	@echo "  run-basic       - Build and run basic demo"
	@echo "  run-vulns       - Build and run vulnerability demo"
	@echo "  run-analyzer    - Build and run analyzer"
	@echo "  run-all         - Run all demos"
	@echo ""
	@echo "  clean           - Remove build artifacts"
	@echo "  help            - Show this help"
	@echo ""
	@echo "Platform: $(PLATFORM)"

# Debug info
.PHONY: info
info:
	@echo "Build Configuration:"
	@echo "  Platform: $(PLATFORM)"
	@echo "  CC: $(CC)"
	@echo "  CFLAGS: $(CFLAGS)"
	@echo "  LDFLAGS: $(LDFLAGS)"
	@echo ""
	@echo "Directories:"
	@echo "  SRC_DIR: $(SRC_DIR)"
	@echo "  BUILD_DIR: $(BUILD_DIR)"
	@echo "  OBJ_DIR: $(OBJ_DIR)"
	@echo ""
	@echo "Targets:"
	@echo "  Examples: $(EXAMPLE_BINS)"
	@echo "  Tools: $(TOOL_BINS)"
