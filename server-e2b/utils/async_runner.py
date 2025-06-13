"""
Async runner utility for executing async functions in Flask context.
This helps bridge the gap between Flask's sync nature and E2B's async SDK.
"""
import asyncio
import threading
import logging
from typing import Callable, Any
from concurrent.futures import Future

logger = logging.getLogger(__name__)


class AsyncRunner:
    """Manages async execution in a dedicated thread with event loop"""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._started = False
    
    def start(self):
        """Start the async runner thread"""
        if self._started:
            return
            
        self._started = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        
        # Wait for loop to be ready
        while self._loop is None:
            threading.Event().wait(0.01)
    
    def _run_event_loop(self):
        """Run the event loop in a separate thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    def run_async(self, coro) -> Future:
        """Schedule an async coroutine and return a Future"""
        if not self._started:
            self.start()
            
        return asyncio.run_coroutine_threadsafe(coro, self._loop)
    
    def stop(self):
        """Stop the event loop and thread"""
        if self._loop and self._started:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)
            self._started = False


# Global async runner instance
async_runner = AsyncRunner()


def run_async_task(async_func: Callable, *args, **kwargs) -> Any:
    """
    Helper function to run an async function from sync code.
    
    Args:
        async_func: The async function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the async function
    """
    # Ensure the runner is started
    async_runner.start()
    
    # Create coroutine
    coro = async_func(*args, **kwargs)
    
    # Schedule and wait for result
    future = async_runner.run_async(coro)
    
    # Wait for completion with a reasonable timeout
    try:
        result = future.result(timeout=kwargs.get('timeout', 600))  # 10 minutes default
        return result
    except Exception as e:
        logger.error(f"Async task failed: {str(e)}")
        raise