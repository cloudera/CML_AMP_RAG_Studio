"""This module contains exceptions and related utilities."""

# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
# ##############################################################################

import contextlib
import functools
import inspect
import logging
from collections.abc import Callable, Iterator
from typing import Awaitable, ParamSpec, Type, TypeVar, Union

import requests
from fastapi import HTTPException

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _exception_propagation() -> Iterator[None]:
    """
    Context manager for catching exceptions and propagating them as :class:`fastapi.HTTPException`s.

    For use in :func:`propagates`.

    Raises
    ------
    :class:`fastapi.HTTPException`

    """
    try:
        yield
    except HTTPException:
        # upstream code already wrapped exception; simply re-raise
        logger.exception("Encountered error")
        raise
    except requests.exceptions.HTTPError as e:
        # propagate upstream HTTP error's message and status code
        logger.exception("Encountered upstream HTTP error")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=e.response.text,
        ) from e
    except Exception as e:
        # unhandled exception; wrap as HTTP 500
        logger.exception("Encountered internal error")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        ) from e


def propagates(f: Callable[P, T]) -> Union[Callable[P, T], Callable[P, Awaitable[T]]]:
    """
    Function decorator for catching and propagating exceptions back to a client.

    For use with FastAPI path operations.

    Examples
    --------

    .. code-block:: python
        :emphasize-lines: 2

        @router.get("/banana")
        @exceptions.propagates
        def banana():
            raise NotImplementedError("Yes! We Have No Bananas")

    returns::

        HTTP/1.1 500 Internal Server Error
        content-length: 36
        content-type: application/json
        server: uvicorn

        {
            "detail": "Yes! We Have No Bananas"
        }

    """

    if inspect.iscoroutinefunction(f):
        # for coroutines, the wrapper must be declared async,
        # and the wrapped function's result must be awaited
        @functools.wraps(f)
        async def exception_propagation_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with _exception_propagation():
                ret: T = await f(*args, **kwargs)
                return ret
    else:

        @functools.wraps(f)
        def exception_propagation_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with _exception_propagation():
                return f(*args, **kwargs)

    return exception_propagation_wrapper
