"""
Process pools that survive a worker dying mid-task.
"""

from __future__ import annotations

import time
from typing import Any
from typing import Callable



__all__ = ["map_watchdog"]


def map_watchdog(pool: Any, fn: Callable[[Any], Any], tasks: list[Any], lost: Callable[[Any], Any],
                 stall_timeout: float = 3600.0, log_every: int = 50) -> list[Any]:
    """`pool.map(fn, tasks)` that survives a worker dying mid-task.

    A `multiprocessing.Pool` replaces a worker that dies (e.g. a segfault inside LIEF on a malformed file), but the task
    it held never returns, so `pool.map` waits forever (run 122's first launch hung this way). Here each task is
    submitted on its own; when no task has finished for `stall_timeout` seconds, the unfinished ones are reported, given
    `lost(task)` as their result, and the pool is terminated.

    Args:
        pool: An open `multiprocessing.Pool`.
        fn: The worker function.
        tasks: Its inputs, one per call.
        lost: Builds the result row for a task that never returned.
        stall_timeout: Seconds without any completion before the unfinished tasks are declared lost (one hour, the
            user's limit, session 85: a task still running then is given up and its file discarded from the analysis).
        log_every: Print progress every this many completions.

    Returns:
        The results, in the order of `tasks`.
    """
    if stall_timeout <= 0:
        raise ValueError(f"stall_timeout must be positive, got {stall_timeout}.")
    pending = {i: pool.apply_async(fn, (t,)) for i, t in enumerate(tasks)}
    results: list[Any] = [None] * len(tasks)
    t0 = last = time.time()
    while pending:
        finished = [i for i, a in pending.items() if a.ready()]
        for i in finished:
            results[i] = pending.pop(i).get()
        done = len(tasks) - len(pending)
        if finished:
            last = time.time()
            if done // log_every != (done - len(finished)) // log_every or not pending:
                print(f"  progress: {done}/{len(tasks)} tasks in {time.time() - t0:.0f}s", flush=True)
        elif time.time() - last > stall_timeout:
            for i in pending:
                print(f"  LOST task {i} (no result after {stall_timeout:.0f}s of no progress: over the limit, or its worker died): "
                      f"{str(tasks[i][:3])[:120]}", flush=True)
                results[i] = lost(tasks[i])
            pool.terminate()
            break
        else:
            time.sleep(5)
    return results
