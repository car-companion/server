# Contributing to Car Companion

First off, thank you for considering contributing to Car Companion! It's people like you that make Car Companion such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](./CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for Car Companion. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps which reproduce the problem** in as many details as possible.
* **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
* **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead and why.**
* **Include screenshots and animated GIFs** if possible.
* **Include your environment details** such as OS, Python version, and relevant package versions.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Car Companion, including completely new features and minor improvements to existing functionality.

Before creating enhancement suggestions, please check the existing issues as you might find out that you don't need to create one. When you are creating an enhancement suggestion, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the suggestion.
* **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
* **Provide specific examples to demonstrate the steps** or mockups to illustrate your idea.
* **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
* **Explain why this enhancement would be useful** to most Car Companion users.

### Pull Requests

Please follow these steps to have your contribution considered by the maintainers:

1. Fork the repository and create your branch from `development`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints (using `flake8`).
5. Issue that pull request!

#### Development Process

1. Clone your fork of the repo
   ```bash
   git clone https://github.com/your-username/car-companion-server.git
   ```

2. Install dependencies using Poetry
   ```bash
   poetry install
   ```

3. Create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. Make your changes and commit them using conventional commits
   ```bash
   git commit -m "feat: add new feature"
   ```

5. Push to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

#### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This leads to more readable messages that are easy to follow when looking through the project history.

Some examples:

* feat: add new user authentication endpoint
* fix: resolve race condition in component status update
* docs: update API documentation
* style: remove trailing whitespace
* refactor: restructure vehicle management module
* test: add tests for preferences module
* chore: update dependencies

### Local Development Setup

1. Create your .env file:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=your-db-name
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_HOST=localhost
   DB_PORT=5432
   ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=http://localhost:8000
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

4. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Testing

Before submitting a pull request, make sure all tests pass:

```bash
python manage.py test
```

For test coverage:

```bash
coverage run manage.py test
coverage report
```

### Style Guide

We use Python's [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide. Key points:

* Use 4 spaces for indentation
* Use snake_case for variable and function names
* Keep lines under 100 characters
* Use descriptive variable names
* Add docstrings to all functions and classes

We use `flake8` to enforce these guidelines. Run it before committing:

```bash
flake8 .
```

## Additional Notes

### Issue and Pull Request Labels

We use labels to help us track and manage issues and pull requests. Here's what they mean:

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Improvements or additions to documentation
* `good first issue` - Good for newcomers
* `help wanted` - Extra attention is needed
* `question` - Further information is requested

## Recognition

Contributors who make significant improvements will be recognized in our README.md.

Thank you for contributing to Car Companion!
