.PHONY: requirements requirements-dev sync-deps install install-dev

# Generate requirements.txt from pyproject.toml
requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes --only=main

# Generate requirements-dev.txt from pyproject.toml  
requirements-dev:
	poetry export -f requirements.txt --output requirements-dev.txt --without-hashes

# Sync both requirements files
sync-deps: requirements requirements-dev
	@echo "✅ Requirements files synced with pyproject.toml"

# Install production dependencies
install:
	poetry install --only=main

# Install all dependencies (including dev)
install-dev:
	poetry install

# Update dependencies and sync requirements
update:
	poetry update
	$(MAKE) sync-deps 