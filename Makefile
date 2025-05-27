TOP_DIR := .
SRC_DIR := $(TOP_DIR)/retail_ai
TEST_DIR := $(TOP_DIR)/tests
DIST_DIR := $(TOP_DIR)/dist
LIB_NAME := retail_ai
LIB_VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
LIB := $(LIB_NAME)-$(LIB_VERSION)-py3-none-any.whl
TARGET := $(DIST_DIR)/$(LIB)

ifeq ($(OS),Windows_NT)
    PYTHON := py.exe
else
    PYTHON := python3
endif

UV := uv
UV_SYNC := $(UV) sync 
UV_BUILD := $(UV) build 
RUFF_CHECK := $(UV) run ruff check --fix --ignore E501 
RUFF_FORMAT := $(UV) run ruff format 
FIND := $(shell which find)
RM := rm -rf
CD := cd

.PHONY: all clean distclean dist format help docs-install docs-serve docs-build docs-deploy docs-clean docs-help

all: dist

install: depends 
	$(UV_SYNC) 

dist: install
	$(UV_BUILD)

depends: 
	$(UV_SYNC) 

format: depends
	$(RUFF_CHECK) $(SRC_DIR) $(TEST_DIR)
	$(RUFF_FORMAT) $(SRC_DIR) $(TEST_DIR)


clean: 
	$(FIND) $(SRC_DIR) $(TEST_DIR) -name \*.pyc -exec rm -f {} \;
	$(FIND) $(SRC_DIR) $(TEST_DIR) -name \*.pyo -exec rm -f {} \;


distclean: clean
	$(RM) $(DIST_DIR)
	$(RM) $(SRC_DIR)/*.egg-info 
	$(RM) $(TOP_DIR)/.mypy_cache
	$(FIND) $(SRC_DIR) $(TEST_DIR) \( -name __pycache__ -a -type d \) -prune -exec rm -rf {} \;

test: 
	$(PYTEST) $(TEST_DIR)

help:
	$(info TOP_DIR: $(TOP_DIR))
	$(info SRC_DIR: $(SRC_DIR))
	$(info TEST_DIR: $(TEST_DIR))
	$(info DIST_DIR: $(DIST_DIR))
	$(info )
	$(info $$> make [all|dist|install|clean|distclean|format|depends])
	$(info )
	$(info       all          - build library: [$(LIB)]. This is the default)
	$(info       dist         - build library: [$(LIB)])
	$(info       install      - installs: [$(LIB)])
	$(info       uninstall    - uninstalls: [$(LIB)])
	$(info       clean        - removes build artifacts)
	$(info       distclean    - removes library)
	$(info       format       - format source code)
	$(info       depends      - installs library dependencies)
	@true

docs-install:
	@echo "Installing documentation dependencies..."
	pip install -r requirements-docs.txt

docs-serve:
	@echo "Serving documentation locally..."
	mkdocs serve

docs-build:
	@echo "Building documentation..."
	mkdocs build

docs-deploy:
	@echo "Deploying documentation to GitHub Pages..."
	mkdocs gh-deploy

docs-clean:
	@echo "Cleaning documentation build artifacts..."
	rm -rf site/

docs-help:
	@echo "Documentation commands:"
	@echo "  docs-install  - Install documentation dependencies"
	@echo "  docs-serve    - Serve documentation locally (http://localhost:8000)"
	@echo "  docs-build    - Build documentation for production"
	@echo "  docs-deploy   - Deploy to GitHub Pages"
	@echo "  docs-clean    - Clean build artifacts"

