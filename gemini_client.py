"""
Gemini API client for Claude Skills generation.
Handles all interactions with the Gemini API.
"""

import os
import json
from typing import Optional, List, Dict
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
import yaml
import logging

# Create logger (no console output, only file)
logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini API to generate skills."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Gemini client with configuration."""
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in .env file or environment."
            )
        
        # Get model name from env or config
        self.model_name = os.getenv('GEMINI_MODEL', self.config['gemini']['model'])
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)
        
        # Generation config
        self.generation_config = types.GenerateContentConfig(
            temperature=self.config['gemini']['temperature'],
            max_output_tokens=self.config['gemini']['max_output_tokens'],
        )
        
        # Load system prompt
        with open('prompts/system_prompt.txt', 'r') as f:
            self.system_prompt = f.read()
        
        # Initialize conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Debug log file - will be renamed with skill name later
        self.debug_log_file = None
        self._temp_log_file = f"logs/debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        
        # Configure file-only logging (no console output)
        self.file_handler = logging.FileHandler(self._temp_log_file)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(self.file_handler)
        logger.setLevel(logging.DEBUG)
        # Prevent propagation to root logger (which would print to console)
        logger.propagate = False
    
    def _save_debug_log(self, event: str, data: dict):
        """Save debug information to log file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data
        }
        
        try:
            # Append to temp log file
            log_file = self.debug_log_file or self._temp_log_file
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry, indent=2) + '\n')
            logger.debug(f"Logged {event}")
        except Exception as e:
            logger.error(f"Failed to save debug log: {e}")
    
    def finalize_log(self, skill_name: str):
        """Rename log file to use skill name."""
        if os.path.exists(self._temp_log_file):
            final_log = f"logs/{skill_name}.log"
            try:
                os.rename(self._temp_log_file, final_log)
                self.debug_log_file = final_log
                logger.debug(f"Renamed log to {final_log}")
            except Exception as e:
                logger.error(f"Failed to rename log: {e}")
                self.debug_log_file = self._temp_log_file
    
    def start_conversation(self, user_intent: str, wants_hooks: bool = False) -> str:
        """
        Start a new skill generation conversation.
        
        Args:
            user_intent: User's description of what they want the skill to do
            wants_hooks: Whether the user wants to include hooks in the skill
            
        Returns:
            Initial questions from Gemini
        """
        self.conversation_history = []
        self.wants_hooks = wants_hooks
        
        hooks_context = ""
        if wants_hooks:
            hooks_context = "\n\nThe user wants to include hooks in this skill. Ask about what automatic actions they need (validation, logging, etc.) and which tool events to hook into (PreToolUse, PostToolUse, Stop)."
        
        prompt = f"""{self.system_prompt}

# User's Initial Request
The user wants to create a skill for: "{user_intent}"{hooks_context}

Based on this request, generate 2-3 intelligent questions (maximum 5 total for entire conversation) to understand:
- The specific capabilities needed
- When the skill should trigger
- What tools or permissions it might need
{"- What hooks are needed and when they should run" if wants_hooks else ""}
- Any specific requirements or constraints

NOTE: If the user leaves answers blank, apply best practices and reasonable defaults.

Output only the questions as a numbered list, nothing else."""

        logger.info("Starting conversation with Gemini")
        self._save_debug_log('start_conversation', {
            'user_intent': user_intent,
            'wants_hooks': wants_hooks,
            'prompt': prompt
        })
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config
            )
            questions = response.text.strip()
            
            logger.info(f"Received questions from Gemini: {len(questions)} chars")
            self._save_debug_log('questions_generated', {
                'questions': questions,
                'response_length': len(questions)
            })
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            self._save_debug_log('error_generating_questions', {
                'error': str(e),
                'error_type': type(e).__name__
            })
            raise
        
        # Track conversation
        self.conversation_history.append({
            'role': 'user',
            'content': f"User intent: {user_intent}"
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': questions
        })
        
        return questions
    
    def ask_followup_questions(
        self, 
        previous_answers: List[str],
        questions_asked: int
    ) -> Optional[str]:
        """
        Generate follow-up questions based on previous answers.
        
        Args:
            previous_answers: List of user's answers so far
            questions_asked: Number of questions asked so far
            
        Returns:
            Follow-up questions or None if enough information gathered
        """
        max_questions = self.config['questions']['max_questions']
        
        if questions_asked >= max_questions:
            return None
        
        # Build context from conversation
        context = "\n\n".join([
            f"{item['role'].upper()}: {item['content']}"
            for item in self.conversation_history
        ])
        
        # Add latest answers and track which were skipped
        skipped_topics = []
        for i, answer in enumerate(previous_answers[len([h for h in self.conversation_history if h['role'] == 'user']) - 1:], 1):
            if not answer or not answer.strip():
                context += f"\n\nUSER ANSWER {i}: [SKIPPED - User wants to use best practices for this]"
                skipped_topics.append(i)
            else:
                context += f"\n\nUSER ANSWER {i}: {answer}"
            
            self.conversation_history.append({
                'role': 'user',
                'content': f"Answer: {answer}" if answer and answer.strip() else "[Skipped]"
            })
        
        questions_remaining = max_questions - questions_asked
        
        skip_instruction = ""
        if skipped_topics:
            skip_instruction = "\n\nIMPORTANT: The user skipped some questions. DO NOT ask follow-up questions about those skipped topics - they want to use best practices. Focus on other aspects if needed."
        
        prompt = f"""{context}

You have {questions_remaining} questions remaining (maximum {max_questions} total).{skip_instruction}

Based on the conversation so far, do you need more information to create an excellent skill? 

If YES: Generate 1-2 targeted follow-up questions to clarify important details (but DO NOT repeat topics the user skipped).
If NO: Respond with exactly: "READY_TO_GENERATE"

Output only the questions or "READY_TO_GENERATE", nothing else."""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.generation_config
        )
        result = response.text.strip()
        
        if result == "READY_TO_GENERATE":
            return None
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': result
        })
        
        return result
    
    def generate_skill(self) -> str:
        """
        Generate the final SKILL.md content based on the conversation.
        
        Returns:
            Complete SKILL.md file content
        """
        # Build full context
        context = "\n\n".join([
            f"{item['role'].upper()}: {item['content']}"
            for item in self.conversation_history
        ])
        
        prompt = f"""{self.system_prompt}

# Conversation History
{context}

# Your Task
Based on the entire conversation above, generate a complete, production-ready SKILL.md file.

IMPORTANT: If the user left answers blank, apply best practices and make reasonable decisions for those aspects.

CRITICAL YAML REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:

1. For descriptions longer than 80 characters, use folded block scalar:
   description: >
     Your multi-line text here
     will be folded into one line.

2. For lists/arrays, use proper YAML format:
   allowed-tools:
     - Bash
     - Read

3. Example valid frontmatter:
   ---
   name: my-skill
   description: >
     This tool helps with data analysis tasks.
   allowed-tools:
     - Bash
   ---

Requirements:
1. YAML frontmatter must be between --- markers
2. Use folded scalar (>) for descriptions over 80 chars
3. Use proper list format for all arrays
4. Write clear markdown instructions
5. Include examples
6. ALL YAML MUST BE PARSEABLE

Output ONLY the raw SKILL.md content. No explanations, no code fences."""

        logger.info("Generating final skill from conversation")
        self._save_debug_log('generate_skill_start', {
            'conversation_length': len(self.conversation_history),
            'context_length': len(context),
            'prompt': prompt
        })
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config
            )
            skill_content = response.text.strip()
            
            logger.info(f"Generated skill content: {len(skill_content)} chars")
            
            # Save generated content to log
            self._save_debug_log('skill_generated', {
                'content_length': len(skill_content),
                'content_preview': skill_content[:500],
                'full_content': skill_content
            })
        except Exception as e:
            logger.error(f"Failed to generate skill: {e}")
            self._save_debug_log('error_generating_skill', {
                'error': str(e),
                'error_type': type(e).__name__
            })
            raise
        
        # Remove code fences if Gemini added them despite instructions
        if skill_content.startswith('```'):
            lines = skill_content.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
            skill_content = '\n'.join(lines)
        
        return skill_content
