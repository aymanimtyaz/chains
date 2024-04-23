from typing import Callable

from chains.src.public_interface import Request, Response

RequestHandler = Callable[[Request], Response]
