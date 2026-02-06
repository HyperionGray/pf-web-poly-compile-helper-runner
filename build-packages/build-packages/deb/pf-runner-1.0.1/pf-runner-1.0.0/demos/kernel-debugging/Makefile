# Makefile for Automagic Demo

CC = gcc
CFLAGS = -g -O0 -Wall -Wno-deprecated-declarations
TARGET = vulnerable_parser
SRC = examples/vulnerable_parser.c

.PHONY: all clean test demo

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $<
	@echo ""
	@echo "✓ Built $(TARGET) with debug symbols"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run automagic analysis: pf kernel-automagic-analysis binary=./$(TARGET)"
	@echo "  2. Or run individual tools:"
	@echo "     - pf kernel-parse-detect binary=./$(TARGET)"
	@echo "     - pf kernel-complexity-analyze binary=./$(TARGET)"
	@echo "     - pf kernel-fuzz-in-memory binary=./$(TARGET) function=parse_command"

clean:
	rm -f $(TARGET) *.json *.txt *.dot
	@echo "Cleaned build artifacts"

test: $(TARGET)
	@echo "Creating test input file..."
	@echo "name=test" > test_input.txt
	@echo "value=123" >> test_input.txt
	@echo ""
	@echo "Running $(TARGET)..."
	@./$(TARGET) test_input.txt
	@echo ""
	@echo "✓ Basic test passed"

demo: $(TARGET)
	@echo "=========================================="
	@echo "  Automagic Parse Function Detection Demo"
	@echo "=========================================="
	@echo ""
	@echo "[1/4] Detecting parse functions..."
	@echo "--------------------------------------"
	@cd ../.. && python3 tools/debugging/vulnerability/parse_function_detector.py demos/kernel-debugging/$(TARGET) --no-r2 | head -50
	@echo ""
	@echo "[2/4] Analyzing complexity..."
	@echo "--------------------------------------"
	@cd ../.. && python3 tools/debugging/vulnerability/complexity_analyzer.py demos/kernel-debugging/$(TARGET) | head -50
	@echo ""
	@echo "[3/4] Scanning vulnerabilities..."
	@echo "--------------------------------------"
	@cd ../.. && python3 tools/debugging/vulnerability/scan_vulnerabilities.py demos/kernel-debugging/$(TARGET) | head -40
	@echo ""
	@echo "[4/4] In-memory fuzzing setup..."
	@echo "--------------------------------------"
	@echo "Use: pf kernel-fuzz-in-memory binary=./$(TARGET) function=parse_command"
	@echo ""
	@echo "=========================================="
	@echo "  Demo Complete!"
	@echo "=========================================="
	@echo ""
	@echo "See AUTOMAGIC-DEMO.md for detailed walkthrough"

help:
	@echo "Automagic Demo Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all    - Build vulnerable_parser (default)"
	@echo "  clean  - Remove build artifacts"
	@echo "  test   - Build and run basic test"
	@echo "  demo   - Run full automagic analysis demo"
	@echo "  help   - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make"
	@echo "  make demo"
	@echo "  make clean"
