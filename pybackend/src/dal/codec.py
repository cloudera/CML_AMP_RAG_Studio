import datetime
import zlib
from typing import Any, Type, TypeVar

import msgpack
from pydantic import BaseModel


def decode_entry(obj: Any) -> Any:
    if isinstance(obj, dict) and "__datetime__" in obj:
        return datetime.datetime.fromisoformat(obj["as_str"].replace("Z", "+00:00"))
    return obj


def encode_entry(obj: Any) -> Any:
    if isinstance(obj, datetime.datetime):
        return {"__datetime__": True, "as_str": obj.isoformat()}
    return obj


def recursive_decode(obj: Any) -> Any:
    obj = decode_entry(obj)
    if isinstance(obj, dict):
        return {k: recursive_decode(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [recursive_decode(v) for v in obj]
    return obj


def recursive_encode(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: recursive_encode(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [recursive_encode(v) for v in obj]
    return encode_entry(obj)


T = TypeVar("T", bound=BaseModel)


def decode_blob(cls: Type[T], data: bytes) -> T:
    # Decompress with zlib
    decompressed_bytes = zlib.decompress(data)
    # Decode with msgpack
    model = msgpack.unpackb(decompressed_bytes)
    # Recursively decode the model
    model = recursive_decode(model)
    return cls.model_validate(model)


def encode_blob(obj: T) -> bytes:
    model = obj.model_dump()
    # Recursively encode the model
    model = recursive_encode(model)
    # Encode with msgpack
    model_bytes = msgpack.packb(model)
    # Compress with zlib
    compressed_bytes = zlib.compress(model_bytes)
    return compressed_bytes
