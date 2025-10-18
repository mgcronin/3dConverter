# Contributing to OBJ to GLB Converter

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Sample files if applicable

### Suggesting Enhancements

We welcome feature requests! Please open an issue with:
- A clear description of the enhancement
- Use cases for the feature
- Any relevant examples or mockups

### Pull Requests

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** for any new functionality
4. **Ensure all tests pass** by running `pytest`
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

### Development Setup

```bash
# Clone the repository
git clone https://github.com/mgcronin/3dConverter.git
cd 3dConverter

# Install in development mode
pip install -e .
pip install -e ".[dev]"

# Run tests
pytest
```

### Coding Standards

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and modular
- Write unit tests for new features

### Testing

- All new features should include tests
- Aim for high test coverage
- Test both success and failure cases
- Use pytest fixtures for common test setup

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep the first line under 50 characters
- Add details in the body if needed

### Questions?

Feel free to open an issue for any questions about contributing!

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive community.

