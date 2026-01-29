"""
Question engine for interactive skill generation.
Manages the Q&A flow with users.
"""

import re
from typing import List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown


class QuestionEngine:
    """Manages interactive Q&A flow for skill generation."""
    
    def __init__(self, max_questions: int = 5):
        """Initialize the question engine."""
        self.max_questions = max_questions
        self.console = Console()
        self.answers: List[str] = []
        self.questions_asked = 0

    def _render_markdown_panel(self, content: str, title: str, border_style: str = "green"):
        """Render LLM output with Markdown formatting (bold/italic/code) inside a panel.

        Falls back to plain rendering if Rich's Markdown parser hits malformed input.
        """
        if not content or not content.strip():
            return

        try:
            md = Markdown(content, code_theme="monokai", justify="left")
            self.console.print(Panel(md, title=title, border_style=border_style))
        except Exception:
            # Graceful fallback so a bad Markdown block doesn't break the flow
            self.console.print(Panel(content, title=title, border_style=border_style))
        self.console.print()
    
    def display_welcome(self):
        """Display welcome message."""
        welcome = """
# 🎯 Claude Skills Generator

This tool will help you create a high-quality Claude Skill by asking a few targeted questions.
        """
        self._render_markdown_panel(welcome, title="Welcome", border_style="blue")
    
    def get_output_location(self, prefs_manager=None) -> str:
        """
        Ask user where to save the skill (doesn't count toward question limit).
        
        Args:
            prefs_manager: Optional PreferencesManager to load/save preference
            
        Returns:
            'personal' or 'project'
        """
        # Get saved preference
        saved_location = prefs_manager.get_output_location() if prefs_manager else None
        
        # Set default based on saved preference
        if saved_location == 'personal':
            default_choice = "1"
        else:
            default_choice = "2"  # Default to project
        
        self.console.print("[bold cyan]📁 Where would you like to save your skill?[/bold cyan]")
        self.console.print()
        self.console.print("  [cyan]1.[/cyan] Personal (~/.claude/skills/) - Available across all your projects")
        self.console.print("  [cyan]2.[/cyan] Project (.claude/skills/) - Only in this repository")
        
        if saved_location:
            saved_text = "personal" if saved_location == "personal" else "project"
            self.console.print(f"  [dim](Last used: {saved_text})[/dim]")
        
        self.console.print()
        
        choice = Prompt.ask(
            "Choose location",
            choices=["1", "2", "personal", "project"],
            default=default_choice
        )
        
        if choice in ["1", "personal"]:
            location = "personal"
            self.console.print("[dim]✓ Will save to ~/.claude/skills/[/dim]")
        else:
            location = "project"
            self.console.print("[dim]✓ Will save to .claude/skills/[/dim]")
        
        # Save preference
        if prefs_manager:
            prefs_manager.set_output_location(location)
        
        self.console.print()
        return location
    
    def get_hooks_preference(self) -> bool:
        """
        Ask user if they want to include hooks (doesn't count toward question limit).
        
        Returns:
            True if user wants hooks, False otherwise
        """
        self.console.print("[bold cyan]🔗 Would you like to include hooks for this skill?[/bold cyan]")
        self.console.print("[dim]Hooks allow automatic actions when the skill is used (e.g., validation, logging)[/dim]")
        self.console.print()
        
        wants_hooks = Confirm.ask(
            "Include hooks?",
            default=False
        )
        
        if wants_hooks:
            self.console.print("[dim]✓ Will ask about hooks during generation[/dim]")
        else:
            self.console.print("[dim]✓ No hooks will be included[/dim]")
        
        self.console.print()
        return wants_hooks
    
    def get_initial_intent(self) -> str:
        """Get the user's initial description of what they want."""
        self.console.print("[bold cyan]Let's start![/bold cyan]", style="bold")
        self.console.print()
        
        intent = Prompt.ask(
            "[yellow]What would you like your Claude Skill to do?[/yellow]\n"
            "Describe the task or capability you want to teach Claude"
        )
        
        self.console.print()
        return intent
    
    def ask_questions(self, questions: str) -> List[str]:
        """
        Display questions and collect answers.
        
        Args:
            questions: Questions from Gemini (numbered list)
            
        Returns:
            List of user answers
        """
        self._render_markdown_panel(
            questions,
            title=f"Questions ({self.questions_asked + 1}-{self.questions_asked + questions.count(chr(10)) + 1})",
            border_style="green"
        )
        
        # Parse questions
        question_lines = [
            line.strip() 
            for line in questions.split('\n') 
            if line.strip() and any(line.strip().startswith(f"{i}.") for i in range(1, 10))
        ]
        
        answers = []
        for i, question in enumerate(question_lines, 1):
            # Remove numbering from question
            clean_question = re.sub(r'^\d+\.\s*', '', question)
            
            answer = Prompt.ask(f"[cyan]{i}.[/cyan] {clean_question}")
            
            # Allow empty answers - user can skip questions
            if not answer or not answer.strip():
                self.console.print("[dim]  (skipped - will use best practices)[/dim]")
                answers.append("")  # Add empty string to maintain question count
            else:
                answers.append(answer)
            
            self.questions_asked += 1
            self.console.print()
        
        self.answers.extend(answers)
        return answers
    
    def confirm_generation(self) -> bool:
        """Ask user if they're ready to generate the skill."""
        self.console.print()
        return Confirm.ask(
            "[yellow]Ready to generate your skill?[/yellow]",
            default=True
        )
    
    def display_generating(self):
        """Display generating message."""
        self.console.print()
        self.console.print("[bold green]✨ Generating your skill...[/bold green]")
        self.console.print()
    
    def display_skill_preview(self, content: str):
        """Display a preview of the generated skill."""
        # Extract just the frontmatter for preview
        lines = content.split('\n')
        frontmatter_end = 0
        dash_count = 0
        
        for i, line in enumerate(lines):
            if line.strip() == '---':
                dash_count += 1
                if dash_count == 2:
                    frontmatter_end = i
                    break
        
        preview_lines = lines[:min(frontmatter_end + 5, len(lines))]
        preview = '\n'.join(preview_lines)
        
        if len(lines) > frontmatter_end + 5:
            preview += '\n...\n(and more)'

        self.console.print(Panel(
            preview,
            title="Generated Skill Preview",
            border_style="green"
        ))

        # Also show a formatted markdown preview of the instruction body so bold/italic render properly
        body = self._extract_markdown_body(content)
        if body:
            truncated = self._truncate_for_preview(body)
            self._render_markdown_panel(
                truncated,
                title="Rendered Markdown Preview",
                border_style="cyan"
            )
    
    def display_success(self, filepath: str):
        """Display success message with filepath."""
        self.console.print()
        self.console.print(
            f"[bold green]✅ Success![/bold green] Skill saved to: [cyan]{filepath}[/cyan]"
        )
        self.console.print()
        self.console.print("[dim]To use this skill:[/dim]")
        self.console.print("[dim]1. Ask Claude: 'What skills are available?'[/dim]")
        self.console.print("[dim]2. Test it by asking Claude to perform the task[/dim]")
        self.console.print()
    
    def display_error(self, errors: List[str], content: str = None, log_file: str = None):
        """Display validation errors with debugging info."""
        self.console.print()
        self.console.print("[bold red]❌ Validation Errors:[/bold red]")
        for error in errors:
            self.console.print(f"  [red]•[/red] {error}")
        
        if content:
            self.console.print()
            self.console.print("[yellow]Generated content preview:[/yellow]")
            preview = content[:500] if len(content) > 500 else content
            self.console.print(f"[dim]{preview}...[/dim]" if len(content) > 500 else f"[dim]{preview}[/dim]")
        
        if log_file:
            self.console.print()
            self.console.print(f"[dim]Debug log saved to: {log_file}[/dim]")
        
        self.console.print()

    def _extract_markdown_body(self, content: str) -> str:
        """Return the markdown body after YAML frontmatter."""
        if not content:
            return ""

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) == 3:
                return parts[2].strip()
        return content.strip()

    def _truncate_for_preview(self, text: str, max_lines: int = 80, max_chars: int = 4000) -> str:
        """Trim long markdown so we don't flood the terminal."""
        if not text:
            return ""

        lines = text.splitlines()
        truncated_lines = lines[:max_lines]
        truncated_text = "\n".join(truncated_lines)

        if len(lines) > max_lines:
            truncated_text += "\n..."

        if len(truncated_text) > max_chars:
            truncated_text = truncated_text[:max_chars] + "\n..."
        return truncated_text
