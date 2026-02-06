# Contributing to Swiss Federal Court Data Generation

First off, thank you for considering contributing to this project! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/Swiss-federal-court-data-generation.git
   cd Swiss-federal-court-data-generation
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/your-org/Swiss-federal-court-data-generation.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Install all dependencies including dev
uv sync

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
uv run pytest tests/test_specific.py -v
```

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Type checking
make typecheck
```

## Making Changes

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** and ensure:
   - Tests pass: `make test`
   - Linting passes: `make lint`
   - Code is formatted: `make format`

3. **Write tests** for new functionality

4. **Update documentation** if needed

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/). Each commit message should be structured as:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or correcting tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

### Examples

```bash
feat(llm): add support for Claude 3.5 Sonnet
fix(processor): handle empty citation references
docs(readme): update installation instructions
test(quality): add tests for quality gate threshold
```

## Pull Request Process

1. **Update your branch** with the latest changes from upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub

4. **Fill out the PR template** completely

5. **Wait for review** - maintainers will review your PR

6. **Address feedback** if any changes are requested

7. **Celebrate** when your PR is merged! 🎉

### PR Requirements

- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow conventional commits
- [ ] PR description explains the changes

## Style Guidelines

### Python Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Line length: 100 characters
- Use type hints for all function signatures
- Write docstrings for public functions and classes

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep README up to date

### Testing Style

- Write descriptive test names
- Use pytest fixtures for common setup
- Aim for high test coverage on new code

## Questions?

Feel free to open an issue if you have questions or need help getting started!

Thank you for contributing! ❤️
