from typing import Any, Coroutine


async def await_or_not(result: Any) -> Any:
    return await result if isinstance(result, Coroutine) else result
