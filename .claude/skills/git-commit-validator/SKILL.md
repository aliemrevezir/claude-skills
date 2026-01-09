---
name: git-commit-validator
description: Validates and formats git commit messages using Conventional Commits standards. Use when the user wants to commit changes, write a commit message, or perform git operations. Triggers on keywords like "git commit", "commit message", "conventional commits", and "stage changes".
allowed-tools: [Bash, Read, Write, Edit]
hooks:
  PreToolUse:
    - matcher: "git commit"
      hooks:
        - type: command
          command: "echo 'Verifying commit message format...'"
---

# Git Commit Validator

This skill ensures all git commit messages follow the **Conventional Commits** specification. It helps maintain a clean, readable, and machine-parseable project history.

## Commit Message Standards

Every commit message must follow this structure:
`<type>[optional scope]: <description>`

`[optional body]`

`[optional footer(s)]`

### 1. Allowed Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

### 2. Formatting Rules
- **Header Length**: Keep the subject line under 72 characters (ideally 50).
- **Case**: The description must be in lowercase.
- **Punctuation**: Do not end the subject line with a period.
- **Imperative Mood**: Use the imperative mood in the description (e.g., "add feature" instead of "added feature").
- **Body**: Use a blank line between the subject and the body.

## Validation Workflow

When a commit is requested or a message is proposed:

1.  **Analyze Changes**: Review the staged changes to determine the appropriate `type` and `scope`.
2.  **Validate Format**: Check the proposed message against the rules above.
3.  **Handle Failures**:
    - If the message is invalid, **do not proceed** with the commit.
    - Explain exactly which rule was violated (e.g., "Missing type", "Header too long").
    - **Suggest a corrected version** of the message and ask for user approval before executing the commit.
4.  **Execute**: Once validated or approved, perform the commit using `git commit -m "validated message"`.

## Examples

### Correct Examples
- `feat(auth): add JWT token validation`
- `fix: resolve memory leak in data parser`
- `docs: update installation instructions in README`
- `chore: bump version to 1.2.0`

### Incorrect Examples (and how to fix them)
- `Fixed the bug` -> `fix: resolve bug in [scope]`
- `Adding new login button.` -> `feat(ui): add login button` (remove period, use imperative)
- `really long commit message that goes way over the seventy two character limit for no reason` -> `refactor: shorten commit message header`

## Usage Tips
- If you are unsure of the scope, look at the directory or module name of the affected files.
- If a commit contains multiple types of changes, suggest splitting the commit or use the most significant type.