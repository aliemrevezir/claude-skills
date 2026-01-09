# Quick Start Guide

## Setup (One-Time)

1. **Get your Gemini API key**:

   - Visit: https://aistudio.google.com/apikey
   - Create an API key
   - Copy the key

2. **Configure the tool**:

   ```bash
   cd /Users/aliemrevezir/Documents/github/claude-skills
   cp .env.example .env
   ```

   Edit `.env` and paste your API key:

   ```bash
   GEMINI_API_KEY=your_actual_key_here
   ```

3. **Install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Activate the virtual environment (do this each time):

```bash
source venv/bin/activate
```

Run the generator:

```bash
python skill_generator.py
```

Or with an initial intent:

```bash
python skill_generator.py "Create a skill for code reviews"
```

## What Happens

1. **Choose location**: Personal (~/.claude/skills/) or Project (.claude/skills/)

   - Default: Project
   - This question doesn't count toward the 5-question limit

2. **Describe your intent**: What should the skill do?

3. **Answer questions**: Gemini asks 2-5 intelligent questions

4. **Review & save**: Generated skill is validated and saved

## Example Session

```
python skill_generator.py

🎯 Claude Skills Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Where would you like to save your skill?

  1. Personal (~/.claude/skills/) - Available across all your projects
  2. Project (.claude/skills/) - Only in this repository

Choose location [1/2/personal/project] (2): 2
✓ Will save to .claude/skills/

Let's start!

What would you like your Claude Skill to do?
> Generate commit messages from git diffs

[Gemini asks 2-3 questions...]
```

## Testing

Run the test suite:

```bash
source venv/bin/activate
python test-debug/test_generator.py
```

## Using Generated Skills

After generating a skill:

1. **Check it was created**:

   ```bash
   ls .claude/skills/your-skill-name/
   ```

2. **Ask Claude**:

   ```
   What Skills are available?
   ```

3. **Use it**: Ask Claude to perform the task your skill handles

## Troubleshooting

**"ModuleNotFoundError"**: Activate the virtual environment

```bash
source venv/bin/activate
```

**"GEMINI_API_KEY not found"**: Check your `.env` file has the key

**Skill not showing in Claude**: Make sure the description includes keywords users would naturally say
