# Claude Skills Manager

A powerful CLI toolkit for creating, browsing, and managing Claude Skills. This tool uses Google's Gemini AI to intelligently generate high-quality `SKILL.md` files that extend Claude's capabilities for specific tasks.

## What It Does

Claude Skills Manager streamlines the workflow for creating and managing Claude Skills - specialized markdown files that teach Claude AI how to perform specific tasks. The toolkit provides:

- **Interactive Skill Generation**: AI-powered skill creation through intelligent Q&A
- **Skills Browser**: Browse and import existing skills from your global library
- **Validation Engine**: Automatic validation of YAML frontmatter and markdown structure
- **Preference Management**: Remembers your output location preferences

## Features

- **Gemini-Powered Generation**: Leverages Google's Gemini AI to understand your intent and generate well-structured skills
- **Smart Q&A Flow**: Adaptive questioning (max 5 questions) that gathers just enough information
- **Hooks Support**: Optional Claude Code hooks for automatic actions (validation, logging, etc.)
- **Rich CLI Interface**: Beautiful terminal UI with colors, panels, and intuitive navigation
- **Cross-Project Skills**: Manage both personal (`~/.claude/skills/`) and project-specific (`.claude/skills/`) skills
- **Debug Logging**: Comprehensive logging for troubleshooting generation issues

## Technical Overview

### Architecture

The project follows a modular design with clear separation of concerns:

```
claude-skills/
├── claude_skills.py      # Main CLI entry point with menu system
├── skill_generator.py    # Skill creation workflow orchestrator
├── skills_browser.py     # Interactive skill browser and importer
├── gemini_client.py      # Gemini API integration and conversation management
├── question_engine.py    # Interactive Q&A flow management
├── skill_validator.py    # YAML frontmatter and markdown validation
├── preferences.py        # User preference persistence
├── rate_limit_utils.py   # API rate limit handling utilities
├── config.yaml           # Application configuration
├── prompts/
│   └── system_prompt.txt # Gemini system prompt for skill generation
├── examples/             # Sample generated skills
│   ├── code-formatter-with-hooks/
│   └── commit-message-generator/
└── logs/                 # Debug logs for skill generation sessions
```

### Core Components

| Component            | Purpose                                                       |
| -------------------- | ------------------------------------------------------------- |
| `claude_skills.py`   | Main CLI application with interactive menu (Click-based)      |
| `skill_generator.py` | Orchestrates the skill generation workflow end-to-end         |
| `skills_browser.py`  | Arrow-key navigable browser for importing global skills       |
| `gemini_client.py`   | Handles all Gemini API interactions with conversation history |
| `question_engine.py` | Manages the interactive Q&A user experience                   |
| `skill_validator.py` | Validates generated skills against Claude's specifications    |

### Data Flow

1. **User Intent** -> Question Engine captures initial description
2. **Gemini Conversation** -> AI generates targeted questions based on intent
3. **Interactive Q&A** -> User answers refine understanding (max 5 questions)
4. **Skill Generation** -> Gemini produces complete SKILL.md content
5. **Validation** -> Validator checks YAML frontmatter and markdown structure
6. **Output** -> Skill saved to personal or project directory

## Prerequisites

- Python 3.8 or later
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/aliemrevezir/claude-skills.git
   cd claude-skills
   ```

2. **Create virtual environment** (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Gemini API key:

   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Make scripts executable** (Unix/macOS):
   ```bash
   chmod +x claude_skills.py skill_generator.py skills_browser.py
   ```

## Usage

### Interactive Menu (Recommended)

Launch the main application:

```bash
python claude_skills.py
```

Menu options:

- **[1] Generate New Skill** - Create skills with AI assistance
- **[2] Browse Global Skills** - Import existing skills to your project
- **[3] Help & Documentation** - View detailed usage information
- **[Q] Exit** - Exit the application

### Direct Commands

Skip the menu and jump to specific tools:

```bash
python claude_skills.py generate    # Launch skill generator
python claude_skills.py browse      # Launch skills browser
```

### Skill Generator

Create a new skill interactively:

```bash
python skill_generator.py
```

With initial intent:

```bash
python skill_generator.py "Create a skill for reviewing pull requests"
```

Specify output location:

```bash
python skill_generator.py --output personal   # ~/.claude/skills/
python skill_generator.py --output project    # .claude/skills/
python skill_generator.py --output ~/custom   # Custom path
python skill_generator.py --provider anthropic
```

### Skills Browser

Browse and import skills from your global library:

```bash
python skills_browser.py
```

### Project Importer

Import skills into any other local project (e.g. a repo under `~/Documents/github`):

```bash
python project_importer.py
```

This lets you configure one or more "root" directories, pick a project inside them, then import a skill into that
project's skills folder. Supported targets (switchable in settings, globally saved): `.claude/skills`, `.codex/skills`, `.agent/skills`, `.agents/skills` (çoklu seçim mümkün).

Navigation:

- `↑/↓` - Navigate through skills
- `Enter` - Select and preview skill
- Select `[Exit Browser]` to quit

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
# LLM provider selection (env override: LLM_PROVIDER)
llm:
  provider: "openai" # openai, anthropic, gemini

providers:
  openai:
    base_url: "http://127.0.0.1:8045/v1"
    model: "claude-sonnet-4-20250514"
    temperature: 0.7
    max_output_tokens: 8000

  anthropic:
    base_url: "http://127.0.0.1:8045"
    model: "claude-sonnet-4-5"
    temperature: 0.7
    max_output_tokens: 8000

  gemini:
    model: "gemini-3-flash-preview"
    temperature: 0.7
    max_output_tokens: 4000

# Question generation settings
questions:
  max_questions: 5
  timeout_seconds: 30

# Output settings
output:
  default_location: "project"
  personal_path: "~/.claude/skills/"
  project_path: ".claude/skills/"

# Validation rules
validation:
  max_name_length: 64
  max_description_length: 1024
  min_description_length: 20
  name_pattern: "^[a-z0-9-]+$"
```

## Generated Skill Structure

Each generated skill creates a directory structure:

```
your-skill-name/
├── SKILL.md          # Main skill file (required)
├── README.md         # Documentation (optional, created on request)
└── examples/         # Usage examples (optional)
    └── examples.md
```

## Environment Variables

| Variable             | Description                                  | Default      |
| -------------------- | -------------------------------------------- | ------------ |
| `LLM_PROVIDER`       | Which provider SDK to use (`openai|anthropic|gemini`) | `openai` |
| `DEFAULT_OUTPUT_DIR` | Default output location                      | `personal`   |
| `OPENAI_API_KEY`     | API key for OpenAI / OpenAI-compatible proxy | Required (if `LLM_PROVIDER=openai`) |
| `OPENAI_BASE_URL`    | Base URL for OpenAI / OpenAI-compatible proxy | Required (if `LLM_PROVIDER=openai`) |
| `OPENAI_MODEL`       | Model name for OpenAI-compatible chat         | From `config.yaml` if unset |
| `ANTHROPIC_API_KEY`  | API key for Anthropic / Anthropic-compatible proxy | Required (if `LLM_PROVIDER=anthropic`) |
| `ANTHROPIC_BASE_URL` | Base URL for Anthropic / Anthropic-compatible proxy | Required (if `LLM_PROVIDER=anthropic`) |
| `ANTHROPIC_MODEL`    | Model name for Anthropic messages             | From `config.yaml` if unset |
| `GEMINI_API_KEY`     | Google Gemini API key                         | Required (if `LLM_PROVIDER=gemini`) |
| `GEMINI_MODEL`       | Gemini model to use                            | From `config.yaml` if unset |

## Troubleshooting

### "API key not found"

Ensure you've created `.env` with your API key:

```bash
cp .env.example .env
# Edit .env and add your key
```

If you see `ANTHROPIC_API_KEY missing` but you set it, double-check the spelling: `ANTHROPIC_...` (with the **H**) not `ANTROPHIC_...`.

### Validation Errors

Common issues:

- **Name format**: Must be lowercase with hyphens only (`my-skill-name`)
- **Description length**: Must be 20-1024 characters
- **Missing frontmatter**: File must start with `---`

### Skill Not Triggering in Claude

The `description` field determines when Claude uses your skill. Include natural trigger terms:

```yaml
# Bad
description: "Helps with documents"

# Good
description: >
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms,
  or document extraction.
```

### Rate Limit Errors

The tool includes rate limit handling. If you hit limits:

- Wait a few seconds and retry
- Consider using a different Gemini model
- Check your API quota at Google AI Studio

### "max_tokens must be greater than thinking.budget_tokens"

If you enabled extended thinking (`thinking_budget_tokens` in `config.yaml`), make sure `max_output_tokens` is larger.
The app auto-adjusts this (adds +512), but if you still see it, lower `thinking_budget_tokens` or raise `max_output_tokens`.

## Examples

The `examples/` directory contains sample skills:

- **code-formatter-with-hooks**: Demonstrates hook integration for automatic formatting
- **commit-message-generator**: Simple skill for generating commit messages

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the existing style and includes appropriate tests.

## License

MIT License - see LICENSE file for details.

## Related Resources

- [Claude Skills Documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
- [Claude Skills Best Practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)
- [Google Gemini API](https://ai.google.dev/)
