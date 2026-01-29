"""
Gemini API client for Claude Skills generation.
Handles all interactions with the Gemini API.
"""

import os
import json
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime
from dotenv import load_dotenv
import yaml
import logging
from rate_limit_utils import handle_rate_limit_error, is_rate_limit_error

# Create logger (no console output, only file)
logger = logging.getLogger(__name__)

ProviderName = Literal["openai", "anthropic", "gemini"]


class GeminiClient:
    """Client for interacting with Gemini API to generate skills."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Gemini client with configuration."""
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.provider: ProviderName = self._resolve_provider()
        provider_cfg = self._resolve_provider_config(self.provider)

        self.model_name = self._resolve_model_name(self.provider, provider_cfg)
        self.temperature = float(provider_cfg.get("temperature", 0.7))
        self.max_output_tokens = self._coerce_optional_int(provider_cfg.get("max_output_tokens")) or 4000

        self.thinking_budget_tokens: Optional[int] = self._coerce_optional_int(provider_cfg.get("thinking_budget_tokens"))
        self._thinking_params: Optional[Dict[str, int]] = None
        if self.thinking_budget_tokens is not None:
            if self.max_output_tokens <= self.thinking_budget_tokens:
                logger.warning(
                    "max_output_tokens (%s) is not greater than thinking budget (%s); increasing max_output_tokens automatically.",
                    self.max_output_tokens,
                    self.thinking_budget_tokens
                )
                self.max_output_tokens = self.thinking_budget_tokens + 512
            self._thinking_params = {"type": "enabled", "budget_tokens": self.thinking_budget_tokens}

        # Initialize provider SDK client
        self._client: Any = None
        self._openai_client: Any = None
        self._anthropic_client: Any = None
        self._gemini_model: Any = None

        self._init_provider_client(self.provider, provider_cfg)
        
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

    @staticmethod
    def _coerce_optional_int(value: object) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            try:
                return int(stripped)
            except ValueError:
                raise ValueError(f"Expected an int-like value, got: {value!r}")
        raise ValueError(f"Expected an int-like value, got: {value!r}")

    def _effective_max_tokens(self) -> int:
        if not self._thinking_params:
            return self.max_output_tokens
        budget = self._thinking_params.get("budget_tokens")
        if isinstance(budget, int) and self.max_output_tokens <= budget:
            return budget + 512
        return self.max_output_tokens

    def _resolve_provider(self) -> ProviderName:
        env_provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
        if env_provider in {"openai", "anthropic", "gemini"}:
            return env_provider  # type: ignore[return-value]

        cfg_provider = (
            (self.config.get("llm", {}) or {}).get("provider")
            or (self.config.get("providers", {}) or {}).get("default")
        )
        if isinstance(cfg_provider, str) and cfg_provider.strip().lower() in {"openai", "anthropic", "gemini"}:
            return cfg_provider.strip().lower()  # type: ignore[return-value]

        # Backwards-compatible default: if openai section exists, use it; else fall back to gemini.
        if isinstance(self.config.get("openai"), dict):
            return "openai"
        return "gemini"

    def _resolve_provider_config(self, provider: ProviderName) -> Dict[str, Any]:
        providers = self.config.get("providers")
        if isinstance(providers, dict) and isinstance(providers.get(provider), dict):
            return dict(providers.get(provider) or {})

        # Backwards compatible (older config.yaml layout)
        legacy = self.config.get(provider)
        if isinstance(legacy, dict):
            return dict(legacy)

        # Fallback to top-level openai/gemini keys if present
        if provider == "openai" and isinstance(self.config.get("openai"), dict):
            return dict(self.config.get("openai") or {})
        if provider == "gemini" and isinstance(self.config.get("gemini"), dict):
            return dict(self.config.get("gemini") or {})
        return {}

    def _resolve_model_name(self, provider: ProviderName, provider_cfg: Dict[str, Any]) -> str:
        env_var = {
            "openai": "OPENAI_MODEL",
            "anthropic": "ANTHROPIC_MODEL",
            "gemini": "GEMINI_MODEL",
        }[provider]
        env_val = os.getenv(env_var)
        if env_val and env_val.strip():
            return env_val.strip()
        cfg_val = provider_cfg.get("model")
        if isinstance(cfg_val, str) and cfg_val.strip():
            return cfg_val.strip()
        raise ValueError(
            f"Model name missing for provider '{provider}'. "
            f"Set {env_var} in .env (or set providers.{provider}.model in config.yaml)."
        )

    def _init_provider_client(self, provider: ProviderName, provider_cfg: Dict[str, Any]) -> None:
        if provider == "openai":
            try:
                from openai import OpenAI
            except Exception as e:  # pragma: no cover
                raise RuntimeError(
                    "OpenAI SDK not installed. Install with `pip install openai`."
                ) from e

            base_url = (os.getenv("OPENAI_BASE_URL") or provider_cfg.get("base_url") or "").strip()
            api_key = (os.getenv("OPENAI_API_KEY") or provider_cfg.get("api_key") or "").strip()
            if not base_url:
                raise ValueError(
                    "OPENAI_BASE_URL missing. Set it in .env or providers.openai.base_url in config.yaml."
                )
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY missing. Set it in .env or providers.openai.api_key in config.yaml."
                )
            self._openai_client = OpenAI(base_url=base_url, api_key=api_key)
            self._client = self._openai_client
            return

        if provider == "anthropic":
            try:
                from anthropic import Anthropic
            except Exception as e:  # pragma: no cover
                raise RuntimeError(
                    "Anthropic SDK not installed. Install with `pip install anthropic`."
                ) from e

            base_url = (os.getenv("ANTHROPIC_BASE_URL") or provider_cfg.get("base_url") or "").strip()
            # Backwards-compatible typo: ANTROPHIC_* (missing 'h')
            api_key = (
                os.getenv("ANTHROPIC_API_KEY")
                or os.getenv("ANTROPHIC_API_KEY")
                or provider_cfg.get("api_key")
                or ""
            ).strip()
            if not base_url:
                raise ValueError(
                    "ANTHROPIC_BASE_URL missing. Set it in .env or providers.anthropic.base_url in config.yaml."
                )
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY missing. Set it in .env or providers.anthropic.api_key in config.yaml."
                )
            self._anthropic_client = Anthropic(base_url=base_url, api_key=api_key)
            self._client = self._anthropic_client
            return

        if provider == "gemini":
            api_key = (os.getenv("GEMINI_API_KEY") or provider_cfg.get("api_key") or "").strip()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY missing. Set it in .env or providers.gemini.api_key in config.yaml."
                )

            try:
                import google.generativeai as genai  # type: ignore
            except Exception:
                genai = None  # type: ignore[assignment]

            if genai is None:
                raise RuntimeError(
                    "Gemini SDK not installed. Install with `pip install google-generativeai`."
                )

            genai.configure(api_key=api_key)
            self._gemini_model = genai.GenerativeModel(self.model_name)
            self._client = self._gemini_model
            return

        raise ValueError(f"Unsupported provider: {provider}")

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

    def _generate_text(self, prompt: str) -> str:
        """Generate text using the configured provider."""
        max_tokens = self._effective_max_tokens()

        if self.provider == "openai":
            kwargs: Dict[str, object] = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": max_tokens,
            }
            if self._thinking_params:
                kwargs["thinking"] = self._thinking_params

            try:
                response = self._openai_client.chat.completions.create(**kwargs)
                return (response.choices[0].message.content or "").strip()
            except Exception as e:
                if self._thinking_params and "thinking.budget_tokens" in str(e) and "max_tokens" in str(e):
                    kwargs["max_tokens"] = int(self._thinking_params["budget_tokens"]) + 512
                    response = self._openai_client.chat.completions.create(**kwargs)
                    return (response.choices[0].message.content or "").strip()
                raise

        if self.provider == "anthropic":
            kwargs2: Dict[str, object] = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if self._thinking_params:
                kwargs2["thinking"] = self._thinking_params

            try:
                response = self._anthropic_client.messages.create(**kwargs2)
            except Exception as e:
                if self._thinking_params and "thinking.budget_tokens" in str(e) and "max_tokens" in str(e):
                    kwargs2["max_tokens"] = int(self._thinking_params["budget_tokens"]) + 512
                    response = self._anthropic_client.messages.create(**kwargs2)
                else:
                    raise

            content = getattr(response, "content", None)
            if isinstance(content, list):
                parts: List[str] = []
                for block in content:
                    text = getattr(block, "text", None)
                    if isinstance(text, str) and text:
                        parts.append(text)
                return "\n".join(parts).strip()
            return str(response).strip()

        if self.provider == "gemini":
            try:
                result = self._gemini_model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.temperature,
                        "max_output_tokens": self.max_output_tokens,
                    },
                )
                text = getattr(result, "text", None)
                if isinstance(text, str):
                    return text.strip()
                return str(result).strip()
            except Exception:
                # Fall back to a simple call signature if SDK changes.
                result = self._gemini_model.generate_content(prompt)
                text = getattr(result, "text", None)
                if isinstance(text, str):
                    return text.strip()
                return str(result).strip()

        raise ValueError(f"Unsupported provider: {self.provider}")

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
            questions = self._generate_text(prompt)
            
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
            
            # Check if it's a rate limit error and provide helpful guidance
            if is_rate_limit_error(e):
                print(handle_rate_limit_error(str(e)))
            
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

        result = self._generate_text(prompt)
        
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
            skill_content = self._generate_text(prompt)
            
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
            
            # Check if it's a rate limit error and provide helpful guidance
            if is_rate_limit_error(e):
                print(handle_rate_limit_error(str(e)))
            
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
