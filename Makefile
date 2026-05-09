.PHONY: test test-all test-unit test-integration test-oz test-selftest-oz clean help

PYTHON = ./.venv/bin/python
PYTEST = $(PYTHON) -m pytest

help:
	@echo "sol-callgraph Test Runner"
	@echo ""
	@echo "Available commands:"
	@echo "  make test-all       Run everything (pytest + full oz selftest)"
	@echo "  make test           Run all pytest (unit + integration + oz smoke)"
	@echo "  make test-unit      Run only unit tests"
	@echo "  make test-integration Run only integration tests"
	@echo "  make test-oz        Run OpenZeppelin smoke tests"
	@echo "  make test-selftest-oz Run the full OpenZeppelin self-test script"
	@echo "  make clean          Remove test artifacts and __pycache__"

test-all: test test-selftest-oz

test:
	$(PYTEST)

test-unit:
	$(PYTEST) tests/unit

test-integration:
	$(PYTEST) tests/integration

test-oz:
	$(PYTEST) tests/openzeppelin

test-selftest-oz:
	$(PYTHON) -m sol_callgraph.selftest_openzeppelin

clean:
	rm -rf test-artifacts/
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
