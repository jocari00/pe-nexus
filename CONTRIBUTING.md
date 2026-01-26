# Contributing to PE-Nexus

Thank you for your interest in contributing to PE-Nexus!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/jordi/pe-nexus.git
   cd pe-nexus
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

## Code Standards

- **Linting**: We use `ruff` for linting. Run `ruff check src/` before committing.
- **Type Checking**: We use `mypy` with strict mode. Run `mypy src/`.
- **Testing**: Run `pytest tests/ -v` to execute the test suite.
- **Line Length**: Maximum 100 characters per line.

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add new agent capability`
- `fix: Resolve extraction confidence issue`
- `docs: Update API documentation`
- `test: Add tests for state machine`

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass and linting is clean
4. Submit a pull request with a clear description

## Reporting Issues

Please use GitHub Issues to report bugs or request features. Include:
- Clear description of the issue
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Python version and OS

## Questions?

Open a GitHub Discussion or Issue for questions about contributing.
