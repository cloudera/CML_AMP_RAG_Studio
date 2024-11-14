from typing import Optional, TypeVar

from fastapi import HTTPException

T = TypeVar("T")


def raise_not_found_if_missing(value: Optional[T], message: str) -> T:
    if value is None:
        raise HTTPException(status_code=404, detail=message)
    return value
