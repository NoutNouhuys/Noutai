# Development Guidelines

## Project Structure
- Always read project_structure.md to now what to look for
- Always update project_structure.md if changes in the structure are made

## Testing
Run `pytest` from the repository root before submitting changes. All tests in
`tests/` should pass.

## Coding Conventions
- Python 3.9 is the target runtime (`runtime.txt`).
- Use 4 spaces for indentation.
- Keep lines under 120 characters where practical.
- Prefer f-strings for formatting and include docstrings for public functions
  and classes.

## Pull Requests
- Reference the related issue in the PR description.
- Summarize major changes.
- Confirm that `pytest` completed successfully.

