# Utils package initialization
# This file allows app.utils to be imported as a package
# Import functions from the utils_module to make them available

# Import functions from the utils module
from app.utils_module import (
    validate_inputs,
    is_valid_url,
    validate_url,
    validate_analysis_size,
    validate_value_bricks,
    safe_truncate_text,
    cache_result,
    retry_on_failure,
    safe_json_loads,
    safe_json_dumps,
    format_currency,
    safe_str,
    flatten_and_stringify,
    get_relevance_keywords,
    is_potential_customer_website
)

# Make all functions available when importing the package
__all__ = [
    "validate_inputs",
    "is_valid_url",
    "validate_url",
    "validate_analysis_size",
    "validate_value_bricks",
    "safe_truncate_text",
    "cache_result",
    "retry_on_failure",
    "safe_json_loads",
    "safe_json_dumps",
    "format_currency",
    "safe_str",
    "flatten_and_stringify",
    "get_relevance_keywords",
    "is_potential_customer_website"
] 