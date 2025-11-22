# Contributing to Value Rollercoaster

<div align="center">

# 🎢

**Thank you for your interest in contributing to Value Rollercoaster!**

</div>

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)
- [Questions?](#questions)

---

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

**Before Submitting a Bug Report:**

- Check if the bug has already been reported in [Issues](https://github.com/your-repo/issues)
- Check the [documentation](docs/) to see if it's a known limitation
- Check [Troubleshooting](docs/TROUBLESHOOTING.md) if it exists

**How to Submit a Bug Report:**

1. Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
2. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs. actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages or logs
   - Screenshots if applicable

### 💡 Suggesting Enhancements

**Before Submitting an Enhancement:**

- Check if the enhancement has already been suggested
- Consider if it aligns with the project's mission
- Think about the impact on existing users

**How to Submit an Enhancement:**

1. Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
2. Include:
   - Clear description of the enhancement
   - Use case and benefits
   - Potential implementation approach
   - Impact on existing features

### 📝 Improving Documentation

Documentation improvements are always welcome! Areas that need help:

- Fixing typos or unclear explanations
- Adding examples or use cases
- Translating documentation
- Adding screenshots or diagrams
- Improving code comments

### 💻 Code Contributions

**Types of Contributions:**

- Bug fixes
- New features
- Performance improvements
- Code refactoring
- Test coverage
- Security improvements

---

## Development Setup

### Prerequisites

- **Python 3.8+**
- **Git**
- **API Keys** (for testing):
  - Google Gemini API key
  - OpenAI API key (optional)
  - Perplexity Sonar API key (optional)
- **Qdrant Database** (cloud or local)

### Setup Steps

1. **Fork the repository**

2. **Clone your fork**
   ```bash
   git clone https://github.com/ValueRollerCoaster/ValueRollerCoaster.git
   cd ValueRollerCoaster
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

6. **Run the application**
   ```bash
   streamlit run app/streamlit_app.py
   ```

### Development Guidelines

- **Create a branch** for your changes: `git checkout -b feature/your-feature-name`
- **Write tests** for new features
- **Follow coding standards** (see below)
- **Update documentation** if needed
- **Commit messages** should be clear and descriptive

---

## Pull Request Process

### Before Submitting

1. **Update documentation** if you changed functionality
2. **Add tests** for new features or bug fixes
3. **Ensure all tests pass**: `pytest`
4. **Check code style**: Follow PEP 8
5. **Update CHANGELOG.md** with your changes

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings introduced
- [ ] CHANGELOG.md updated

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
```

### Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

---

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Keep functions focused and small
- Write **docstrings** for functions and classes

### Code Organization

- **Modular design**: Keep related code together
- **Separation of concerns**: Business logic separate from UI
- **DRY principle**: Don't repeat yourself
- **Clear naming**: Use descriptive variable and function names

### Example

```python
def generate_persona(website_url: str, company_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a buyer persona from a website URL.
    
    Args:
        website_url: The URL of the prospect's website
        company_profile: The company profile configuration
        
    Returns:
        A dictionary containing the generated persona data
        
    Raises:
        ValueError: If website_url is invalid
    """
    # Implementation
    pass
```

---

## Documentation

### Documentation Standards

- **Clear and concise**: Write for your audience
- **Examples**: Include practical examples
- **Up-to-date**: Keep docs in sync with code
- **Well-organized**: Use clear headings and structure

### Documentation Types

- **Code comments**: Explain why, not what
- **Docstrings**: Document functions and classes
- **README files**: Overview and quick start
- **User guides**: Step-by-step instructions
- **API documentation**: Technical reference

---

## Questions?

- **GitHub Discussions**: For questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check [docs/](docs/) for detailed guides

---

## Recognition

Contributors will be recognized in:
- **README.md** (Contributors section)
- **Release notes** for significant contributions
- **GitHub contributors page**

---

<div align="center">

**Thank you for contributing to Value Rollercoaster! 🎢**

</div>

