"""
Rate limit utility functions for Gemini API.
Handles rate limit errors and provides user-friendly guidance.
"""

import re
from typing import Optional


class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


def parse_rate_limit_error(error_message: str) -> Optional[dict]:
    """
    Parse a Gemini API rate limit error message.
    
    Args:
        error_message: The error message string from the API
        
    Returns:
        Dictionary with parsed error details or None if not a rate limit error
        {
            'code': int,
            'message': str,
            'retry_after': float (seconds),
            'quota_metric': str,
            'limit': int,
            'model': str
        }
    """
    # Check if it's a 429 RESOURCE_EXHAUSTED error
    if '429 RESOURCE_EXHAUSTED' not in error_message:
        return None
    
    error_info = {
        'code': 429,
        'message': '',
        'retry_after': None,
        'quota_metric': None,
        'limit': None,
        'model': None
    }
    
    # Extract retry time
    retry_match = re.search(r'Please retry in ([\d.]+)s', error_message)
    if retry_match:
        error_info['retry_after'] = float(retry_match.group(1))
    
    # Extract quota metric
    quota_match = re.search(r'metric: ([^,]+)', error_message)
    if quota_match:
        error_info['quota_metric'] = quota_match.group(1)
    
    # Extract limit
    limit_match = re.search(r'limit: (\d+)', error_message)
    if limit_match:
        error_info['limit'] = int(limit_match.group(1))
    
    # Extract model
    # Try to find "model: gemini-X-Y" pattern (only alphanumeric and hyphens)
    model_match = re.search(r'model:\s*([a-z0-9\-]+)', error_message)
    if model_match:
        error_info['model'] = model_match.group(1)
    
    # Extract main message
    message_match = re.search(r"'message': '([^']+)'", error_message)
    if message_match:
        error_info['message'] = message_match.group(1)
    
    return error_info


def handle_rate_limit_error(error_message: str) -> str:
    """
    Handle a rate limit error and provide user guidance.
    
    Args:
        error_message: The error message string from the API
        
    Returns:
        User-friendly error message with guidance
    """
    error_info = parse_rate_limit_error(error_message)
    
    if not error_info:
        return error_message
    
    output = []
    output.append("\n" + "="*70)
    output.append("❌ GEMINI API RATE LIMIT EXCEEDED")
    output.append("="*70)
    
    if error_info['model']:
        output.append(f"\n📊 Model: {error_info['model']}")
    
    if error_info['limit']:
        output.append(f"📈 Daily Limit: {error_info['limit']} requests")
    
    if error_info['retry_after']:
        minutes = int(error_info['retry_after'] // 60)
        seconds = int(error_info['retry_after'] % 60)
        if minutes > 0:
            output.append(f"⏱️  Retry After: {minutes}m {seconds}s")
        else:
            output.append(f"⏱️  Retry After: {seconds}s")
    
    output.append("\n" + "-"*70)
    output.append("💡 ÇÖZÜM:")
    output.append("-"*70)
    output.append("\n1. API anahtarınızı kontrol edin veya yeni bir tane oluşturun:")
    output.append("   🔗 https://aistudio.google.com/u/1/api-keys")
    output.append("\n2. Mevcut kullanımınızı ve limitinizi görüntüleyin:")
    output.append("   🔗 https://ai.dev/rate-limit")
    output.append("\n3. Gemini API fiyatlandırma ve limitler hakkında daha fazla bilgi:")
    output.append("   🔗 https://ai.google.dev/gemini-api/docs/rate-limits")
    output.append("\n" + "="*70 + "\n")
    
    return "\n".join(output)


def is_rate_limit_error(error: Exception) -> bool:
    """
    Check if an exception is a rate limit error.
    
    Args:
        error: The exception to check
        
    Returns:
        True if it's a rate limit error, False otherwise
    """
    error_str = str(error)
    return '429 RESOURCE_EXHAUSTED' in error_str or 'rate limit' in error_str.lower()
