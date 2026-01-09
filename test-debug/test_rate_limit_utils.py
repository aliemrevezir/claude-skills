"""
Test script for rate limit utility functions.
Demonstrates how to use the rate_limit_utils module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rate_limit_utils import (
    parse_rate_limit_error,
    handle_rate_limit_error,
    is_rate_limit_error
)


# Test error message (the one provided by the user)
test_error = """Error: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \\n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, model: gemini-3-flash\\nPlease retry in 23.996516905s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'location': 'global', 'model': 'gemini-3-flash'}, 'quotaValue': '20'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '23s'}]}}"""


def main():
    print("=" * 70)
    print("RATE LIMIT UTILITY TEST")
    print("=" * 70)
    
    # Test 1: Parse error
    print("\n📋 Test 1: Parse Error Information")
    print("-" * 70)
    error_info = parse_rate_limit_error(test_error)
    if error_info:
        print(f"✅ Successfully parsed error:")
        print(f"   Code: {error_info['code']}")
        print(f"   Model: {error_info['model']}")
        print(f"   Limit: {error_info['limit']}")
        print(f"   Retry After: {error_info['retry_after']}s")
        print(f"   Quota Metric: {error_info['quota_metric']}")
    else:
        print("❌ Failed to parse error")
    
    # Test 2: Check if rate limit error
    print("\n📋 Test 2: Detect Rate Limit Error")
    print("-" * 70)
    is_rate_limit = is_rate_limit_error(Exception(test_error))
    print(f"✅ Is rate limit error: {is_rate_limit}")
    
    # Test 3: Handle error (user-friendly message)
    print("\n📋 Test 3: User-Friendly Error Message")
    print("-" * 70)
    user_message = handle_rate_limit_error(test_error)
    print(user_message)
    
    # Test 4: Non-rate-limit error
    print("\n📋 Test 4: Non-Rate-Limit Error")
    print("-" * 70)
    normal_error = "Error: Something else went wrong"
    is_rate_limit = is_rate_limit_error(Exception(normal_error))
    print(f"Is rate limit error: {is_rate_limit}")
    print(f"Handled message: {handle_rate_limit_error(normal_error)[:50]}...")


if __name__ == "__main__":
    main()
