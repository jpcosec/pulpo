"""
Sync/Async Detector for Pulpo Operations

Handles sync functions in async Prefect flows.

Problem: Prefect flows are async, but user operations can be either sync or async.

Solution: Detect sync functions and wrap them with run_in_executor for
compatibility with async flows.
"""

import asyncio
import inspect
from typing import Any, Callable, TypeVar, Union

T = TypeVar("T")


class SyncAsyncDetector:
    """Detects and handles sync/async functions."""

    @staticmethod
    def is_async(func: Callable) -> bool:
        """Check if a function is async.

        Args:
            func: Function to check

        Returns:
            True if function is async
        """
        return inspect.iscoroutinefunction(func)

    @staticmethod
    def is_sync(func: Callable) -> bool:
        """Check if a function is sync.

        Args:
            func: Function to check

        Returns:
            True if function is sync (not async)
        """
        return not SyncAsyncDetector.is_async(func)

    @staticmethod
    def get_signature_info(func: Callable) -> dict[str, Any]:
        """Get function signature information.

        Args:
            func: Function to inspect

        Returns:
            Dictionary with signature info
        """
        sig = inspect.signature(func)

        return {
            "params": list(sig.parameters.keys()),
            "return_annotation": sig.return_annotation,
            "is_async": SyncAsyncDetector.is_async(func),
            "param_count": len(sig.parameters),
        }

    @staticmethod
    def wrap_if_sync(
        func: Callable[..., T],
        executor: str = "threadpool",
    ) -> Callable[..., Any]:
        """Wrap sync function to work in async context.

        If function is already async, returns it unchanged.
        If sync, wraps with run_in_executor for async compatibility.

        Args:
            func: Function to wrap
            executor: "threadpool" (default) or "processpool"

        Returns:
            Async-compatible wrapper function
        """
        if SyncAsyncDetector.is_async(func):
            return func

        async def async_wrapper(*args, **kwargs) -> T:
            """Async wrapper for sync function using run_in_executor."""
            loop = asyncio.get_event_loop()

            # Use thread pool by default (good for I/O-bound)
            # Use process pool for CPU-bound (requires setting executor)
            executor_instance = None
            if executor == "processpool":
                from concurrent.futures import ProcessPoolExecutor

                executor_instance = ProcessPoolExecutor()

            return await loop.run_in_executor(
                executor_instance,
                lambda: func(*args, **kwargs),
            )

        # Preserve function metadata
        async_wrapper.__name__ = func.__name__
        async_wrapper.__doc__ = func.__doc__

        return async_wrapper

    @staticmethod
    def detect_and_wrap(
        func: Callable[..., T],
        executor: str = "threadpool",
    ) -> tuple[Callable[..., Any], bool]:
        """Detect if function needs wrapping and wrap if necessary.

        Args:
            func: Function to process
            executor: "threadpool" (default) or "processpool"

        Returns:
            Tuple of (wrapped_function, was_sync)
        """
        is_sync = SyncAsyncDetector.is_sync(func)
        wrapped = SyncAsyncDetector.wrap_if_sync(func, executor=executor)
        return wrapped, is_sync

    @staticmethod
    def get_wrapper_code(
        func: Callable,
        func_name: str,
        executor: str = "threadpool",
    ) -> str:
        """Generate code for wrapping a sync function to async.

        Useful for code generation.

        Args:
            func: Original function
            func_name: Name to use in generated code
            executor: "threadpool" or "processpool"

        Returns:
            Python code for the wrapper
        """
        if SyncAsyncDetector.is_async(func):
            # Already async, no wrapper needed
            return f"# {func_name} is already async\n"

        if executor == "processpool":
            return f'''
async def {func_name}_wrapped(*args, **kwargs):
    """Async wrapper for {func_name} using ProcessPoolExecutor."""
    from concurrent.futures import ProcessPoolExecutor
    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor()
    return await loop.run_in_executor(
        executor,
        lambda: {func_name}(*args, **kwargs),
    )
'''.strip()
        else:
            # threadpool (default)
            return f'''
async def {func_name}_wrapped(*args, **kwargs):
    """Async wrapper for {func_name} using ThreadPoolExecutor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # Use default ThreadPoolExecutor
        lambda: {func_name}(*args, **kwargs),
    )
'''.strip()

    @staticmethod
    def batch_process(
        functions: dict[str, Callable],
        executor: str = "threadpool",
    ) -> dict[str, tuple[Callable, bool]]:
        """Process multiple functions for async compatibility.

        Args:
            functions: Dict mapping name to function
            executor: "threadpool" or "processpool"

        Returns:
            Dict mapping name to (wrapped_func, was_sync)
        """
        return {
            name: SyncAsyncDetector.detect_and_wrap(func, executor=executor)
            for name, func in functions.items()
        }

    @staticmethod
    def get_execution_strategy(func: Callable) -> str:
        """Get recommended execution strategy for a function.

        Args:
            func: Function to analyze

        Returns:
            "native_async", "thread_pool", or "process_pool"
        """
        if SyncAsyncDetector.is_async(func):
            return "native_async"

        # Heuristic: check function name and docstring for hints
        name = func.__name__.lower()
        doc = (func.__doc__ or "").lower()

        if any(
            keyword in name or keyword in doc
            for keyword in ["cpu", "compute", "process", "intensive"]
        ):
            return "process_pool"

        # Default to thread pool for I/O-bound operations
        return "thread_pool"

    @staticmethod
    def validate_function(func: Callable) -> tuple[bool, str]:
        """Validate that a function can be wrapped.

        Args:
            func: Function to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not callable(func):
            return False, "Function is not callable"

        try:
            sig = inspect.signature(func)
            # Try to bind empty args to check signature is valid
            return True, ""
        except (ValueError, TypeError) as e:
            return False, f"Invalid function signature: {e}"
