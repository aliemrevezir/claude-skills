# Claude Skills Generator 🎯

An interactive command-line tool that uses Gemini AI to help you create high-quality Claude Skills. The tool asks intelligent questions (max 5) to understand your intent, then generates a properly formatted `SKILL.md` file following Claude's official specifications.

## Features

- ✨ **Interactive Q&A**: Smart question generation that adapts based on your answers
- 🤖 **Gemini-Powered**: Uses Google's Gemini AI for intelligent skill generation
- 🔗 **Hooks Support**: Optionally generate skills with Claude Code hooks for automatic actions
- 💾 **Remembers Preferences**: Saves your output location choice for next time
- ✅ **Validation**: Automatic validation of YAML frontmatter and markdown structure
- 🎨 **Beautiful CLI**: Rich console output with colors and formatting
- 📝 **Best Practices**: Follows Claude's official skill authoring guidelines
- 🔧 **Configurable**: Customizable settings for models, output locations, and more

## Installation

1. **Clone the repository** (or navigate to the directory):

   ```bash
   cd /Users/aliemrevezir/Documents/github/claude-skills
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   Or using uv (recommended):

   ```bash
   uv pip install -r requirements.txt
   ```

3. **Set up your Gemini API key**:

   Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Gemini API key:

   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```

   Get your API key from: https://aistudio.google.com/apikey

4. **Make scripts executable**:
   ```bash
   chmod +x claude_skills.py skill_generator.py skills_browser.py
   ```

## Quick Start

The easiest way to get started is with the main CLI application:

```bash
python claude_skills.py
```

This will launch an interactive menu where you can:

- **Generate new skills** with AI assistance
- **Browse and import** global skills
- **View help** and documentation

### Direct Commands

You can also launch specific tools directly:

```bash
python claude_skills.py generate    # Launch skill generator
python claude_skills.py browse      # Launch skills browser
```

## Usage

### Main CLI Application (Recommended)

The unified CLI provides menu-based access to all features:

```bash
python claude_skills.py
```

**Menu Options:**

- **[1] Generate New Skill** - Create skills interactively with AI
- **[2] Browse Global Skills** - Import existing skills to your project
- **[3] Help & Documentation** - View detailed help
- **[Q] Exit** - Exit the application

**Direct Access:**

```bash
python claude_skills.py generate    # Skip menu, go to generator
python claude_skills.py browse      # Skip menu, go to browser
```

### Skills Browser - Import Global Skills

Browse and import skills from your global skills directory to your project:

```bash
python claude_skills.py browse
# OR
python skills_browser.py
```

**Features:**

- 📋 View all skills from `~/.claude/skills/`
- ⬆️⬇️ Navigate with arrow keys
- 👁️ Preview skill details before importing
- ⚡ Import to project with Enter key
- 🔄 Continue browsing and importing multiple skills
- ❌ Exit anytime with the exit option

**Keyboard Shortcuts:**

- `↑/↓` - Navigate through skills
- `Enter` - Select/Import skill
- Select `[Exit Browser]` to quit

This is perfect for:

- Reusing skills across multiple projects
- Sharing skills with your team
- Quickly adding common skills to new projects

### Skill Generator - Create New Skills

Run the tool interactively:

```bash
python claude_skills.py generate
# OR
python skill_generator.py
```

The tool will:

1. Ask what you want your skill to do
2. Ask 2-5 follow-up questions to understand your needs
3. Generate a complete `SKILL.md` file
4. Validate the output
5. Save it to your chosen location

### With Initial Intent

Provide your intent upfront to skip the first prompt:

```bash
python skill_generator.py "Create a skill for reviewing pull requests"
```

### Specify Output Location

Save to personal skills directory (~/.claude/skills/):

```bash
python skill_generator.py --output personal
```

Save to project skills directory (.claude/skills/):

```bash
python skill_generator.py --output project
```

Save to custom location:

```bash
python skill_generator.py --output ~/my-custom-skills
```

### Full Example

```bash
python skill_generator.py "Generate commit messages from git diffs" --output personal
```

## Configuration

Edit `config.yaml` to customize:

- **Gemini Model**: Choose which Gemini model to use
- **Max Questions**: Set the maximum number of questions (default: 5)
- **Output Defaults**: Set default output location
- **Validation Rules**: Customize validation constraints

```yaml
gemini:
  model: "gemini-2.0-flash-exp" # Fast and capable
  temperature: 0.7
  max_output_tokens: 4000

questions:
  max_questions: 5

output:
  default_location: "personal"
```

## What Happens

1. **Choose location**: Personal (~/.claude/skills/) or Project (.claude/skills/)

   - Default: Project
   - This question doesn't count toward the 5-question limit

2. **Optional hooks**: Choose whether to include Claude Code hooks (default: no)

   - Hooks enable automatic actions when the skill is used
   - Also doesn't count toward question limit

3. **Describe your intent**: What should the skill do?

4. **Answer questions**: Gemini asks 2-5 intelligent questions

5. **Review & save**: Generated skill is validated and saved file with:
   - Proper YAML frontmatter
   - Clear instructions
   - Relevant examples
   - Appropriate metadata fields
6. **Validation** ensures the skill follows Claude's specifications

## How It Works

1. **You describe** what you want the skill to do
2. **Gemini asks** intelligent follow-up questions (max 5)
3. **You answer** the questions to refine the requirements
4. **Gemini generates** a complete SKILL.md file with:
   - Proper YAML frontmatter
   - Clear instructions
   - Relevant examples
   - Appropriate metadata fields
5. **Validation** ensures the skill follows Claude's specifications
6. **Output** is saved to your chosen location

## Generated Skill Structure

```
your-skill-name/
├── SKILL.md          # Main skill file (required)
├── README.md         # Documentation (optional)
└── examples/         # Usage examples (optional)
    └── examples.md
```

## Examples

See the `examples/` directory for sample generated skills:

- Simple single-file skills
- Skills with tool restrictions
- Skills with Claude Code hooks for automatic actions
- Skills with supporting documentation

## Troubleshooting

### "GEMINI_API_KEY not found"

Make sure you've:

1. Created a `.env` file (copy from `.env.example`)
2. Added your actual Gemini API key

### Validation Errors

The tool validates generated skills automatically. Common issues:

- **Name format**: Must be lowercase with hyphens only (e.g., `my-skill-name`)
- **Description length**: Must be 20-1024 characters
- **Missing frontmatter**: File must start with `---`

### Generated Skill Not Triggering in Claude

Make sure the `description` field includes keywords that users would naturally say. For example:

❌ Bad: "Helps with documents"
✅ Good: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

## Claude Skills Documentation

For more information about Claude Skills, see:

- [Agent Skills Guide](https://docs.claude.com/en/docs/agents-and-tools/agent-skills)
- [Best Practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)

## Requirements

- Python 3.8+
- Gemini API key
- Dependencies listed in `requirements.txt`

## License

MIT

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review Claude's official Skills documentation
3. Open an issue in this repository
