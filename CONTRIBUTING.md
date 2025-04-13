# Contributing to ML Paper Visualizer

First off, thank you for considering contributing to ML Paper Visualizer! It's people like you that make this tool valuable for the research community.

Following these guidelines helps communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## What kinds of contributions are we looking for?

ML Paper Visualizer is an open-source project, and we welcome contributions from the community. There are many ways to contribute:

- **Reporting Bugs:** If you encounter an error or unexpected behavior.
- **Suggesting Enhancements:** Proposing new features or improvements to existing ones.
- **Improving Documentation:** Fixing typos, clarifying instructions, or adding missing information.
- **Writing Code:** Fixing bugs, implementing new features, or improving performance. This can be for the backend (FastAPI/Python) or frontend (Next.js/TypeScript).
- **Adding Test Cases:** Enhancing the test coverage for backend or frontend components.
- **Submitting Sample Papers:** Providing interesting research papers (if legally permissible to share) that showcase the visualizer's capabilities or challenge its extraction logic (place in `src/samples/`).

## Ground Rules

- **Respectful Communication:** Ensure all interactions are respectful and constructive. We expect participants to adhere to common open-source community standards (consider adding a formal Code of Conduct later).
- **Testing:** Ensure that any code changes include relevant tests (backend: pytest, frontend: Jest) and that all tests pass before submitting a Pull Request. See the `README.md` for instructions on running tests.
- **Keep it Focused:** Try to keep pull requests focused on a single issue or feature.

## Your First Contribution

Unsure where to begin?

- Look for issues tagged `good first issue` or `help wanted`.
- Improve documentation – it's a great way to learn the project structure.
- Add more tests – this helps ensure stability.

Working on your first Pull Request? You can learn how from this _free_ series: [How to Contribute to an Open Source Project on GitHub](https://egghead.io/courses/how-to-contribute-to-an-open-source-project-on-github).

Feel free to ask for help; everyone is a beginner at first!

## Getting Started: Making Changes

1.  **Fork the repository:** Create your own fork of the `ml_paper_visualizer` codebase on GitHub.
2.  **Clone your fork:** `git clone https://github.com/YOUR_USERNAME/ml_paper_visualizer.git`
3.  **Create a branch:** `git checkout -b my-fix-branch main` (or choose a descriptive name).
4.  **Make your changes:** Implement your fix or feature.
5.  **Run tests:** Ensure all backend (`pytest`) and frontend (`npm test` or `pnpm test`) tests pass.
6.  **Commit your changes:** Use clear and descriptive commit messages.
7.  **Push to your fork:** `git push origin my-fix-branch`
8.  **Open a Pull Request:** Submit a pull request to the main `ml_paper_visualizer` repository. Provide a clear description of the changes and link any relevant issues.

_Note: Currently, we do not require a Contributor License Agreement (CLA) or Developer Certificate of Origin (DCO)._

## How to Report a Bug

If you find a bug, please ensure it hasn't already been reported by searching the existing issues.

If you're reporting a new bug, please include:

1.  Your operating system and browser version (if frontend related).
2.  Python version (if backend related).
3.  Node.js version (if frontend related).
4.  Steps to reproduce the bug.
5.  What you expected to happen.
6.  What actually happened (including any error messages or screenshots).

Open an issue on the GitHub repository with the label `bug`.

**Security Vulnerabilities:** If you find a security vulnerability, **do NOT open an issue**. Please email the maintainer directly (replace with actual contact later, e.g., `security@yourprojectdomain.com` or a maintainer's email).

## How to Suggest a Feature or Enhancement

1.  Search existing issues to see if the feature has already been suggested.
2.  If not, open a new issue on GitHub.
3.  Clearly describe the feature you would like to see, why it's needed, and how you envision it working. Use the label `enhancement`.

## Code Review Process

- Maintainers will review Pull Requests regularly.
- Feedback will be provided on the PR. Please respond to feedback within a reasonable timeframe (e.g., two weeks) to keep the PR active.
- Approval from at least one maintainer is required for merging.
- We aim to provide initial feedback within a week, but delays may occur.

## Community

Currently, discussions primarily happen via GitHub Issues and Pull Requests.

_(Optional: Add links to other community channels like Discord, Slack, Gitter, mailing list if they exist)_
