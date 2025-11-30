"""
Helper utility functions for Model Court.
"""

import asyncio
from typing import List, Callable, Any, TypeVar, Coroutine
from functools import wraps

T = TypeVar('T')


async def run_with_concurrency_limit(
    tasks: List[Coroutine[Any, Any, T]],
    limit: int
) -> List[T]:
    """
    Run async tasks with a concurrency limit.
    
    Args:
        tasks: List of coroutines to execute
        limit: Maximum number of concurrent tasks
    
    Returns:
        List of results in the same order as input tasks
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def bounded_task(task: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[bounded_task(task) for task in tasks])


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry async functions on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_verdict(
    objection_ratio: float,
    rules: dict
) -> str:
    """
    Calculate verdict based on objection ratio and rules.
    
    Args:
        objection_ratio: Ratio of objections (0.0-1.0)
        rules: Dictionary of verdict rules
            Example: {
                "supported": {"operator": "eq", "value": 0},
                "suspicious": {"operator": "lt", "value": 0.5},
                "refuted": "default"
            }
    
    Returns:
        Verdict string
    """
    default_verdict = None
    
    for verdict, rule in rules.items():
        if rule == "default":
            default_verdict = verdict
            continue
        
        operator = rule.get("operator")
        value = rule.get("value")
        
        if operator == "eq" and objection_ratio == value:
            return verdict
        elif operator == "lt" and objection_ratio < value:
            return verdict
        elif operator == "le" and objection_ratio <= value:
            return verdict
        elif operator == "gt" and objection_ratio > value:
            return verdict
        elif operator == "ge" and objection_ratio >= value:
            return verdict
    
    # Return default if no rule matched
    return default_verdict or "unknown"

