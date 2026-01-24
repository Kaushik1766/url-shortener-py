import time
import functools

def log_performance(func):
    """Decorator to measure the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        except:
            raise
        finally:
            end_time = time.perf_counter()
            run_time = end_time - start_time
            print(f"Function {func.__name__!r} took {run_time:.4f} seconds to execute.")
    return wrapper