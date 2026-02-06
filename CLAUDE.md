# CLAUDE.md

## Project Overview

**Sova** is a Streamlit-based Python web application. The project is currently in an early/skeleton stage with a single "Hello world" page.

## Repository Structure

```
Sova/
├── Home.py          # Main Streamlit application entry point
├── README.md        # Project readme
├── .gitignore       # Git ignore rules
└── CLAUDE.md        # This file
```

## Tech Stack

- **Language**: Python
- **Framework**: [Streamlit](https://streamlit.io/) — a Python framework for building data-driven web apps
- **Secrets Management**: Streamlit secrets (`.streamlit/secrets.toml`, gitignored)

## Running the Application

```bash
streamlit run Home.py
```

There is no `requirements.txt` or `pyproject.toml` yet. The only dependency is `streamlit`.

## Development Notes

### No Build System

This project has no configured build tooling, linter, formatter, test framework, or CI/CD pipeline.

### No Dependency File

Dependencies are not formally declared. If adding packages, create a `requirements.txt` or `pyproject.toml`.

### Streamlit Conventions

- Page files should be Python scripts that use `import streamlit as st`.
- To add multi-page navigation, create a `pages/` directory with additional `.py` files.
- Secrets go in `.streamlit/secrets.toml` (already gitignored).

## Key Conventions

- The main entry point is `Home.py` at the repository root.
- Sensitive configuration (API keys, secrets) must go in `.streamlit/secrets.toml` and must never be committed.

## Git Practices

- The `main` branch contains the primary codebase.
- Feature branches use the pattern `claude/<description>-<id>` for Claude Code work.
