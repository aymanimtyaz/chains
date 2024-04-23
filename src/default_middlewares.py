from traceback import format_exc
from typing import Callable

from chains.src.request import IRequest
from chains.src.response import IResponse, ResponseV1_1
from chains.src.exceptions import NotFoundException, MethodNotAllowedException


def root_error_handlerv1_1(request: IRequest, next: Callable[[IRequest], IResponse]) -> IResponse:
    try:
        response: IResponse = next(request)
    except NotFoundException as e:
        response: ResponseV1_1 = ResponseV1_1(
            status_code=404,
            status_text="NOT FOUND"
        )
        response.body = str(e)
        response.headers.set_single_value_header(
            name="Content-Type", value="text/plain"
        ).set_single_value_header(
            name="Content-Length", value=len(response.body)
        )
    except MethodNotAllowedException as e:
        response: ResponseV1_1 = ResponseV1_1(
            status_code=405,
            status_text="METHOD NOT ALLOWED"
        )
        response.body = str(e)
        response.headers.set_single_value_header(
            name="Content-Type", value="text/plain"
        ).set_single_value_header(
            name="Content-Length", value=len(response.body)
        ).set_single_value_header(
            name="Allow", value=", ".join(e.allowed_methods)
        )
    except Exception as e:
        response: ResponseV1_1 = ResponseV1_1(
            status_code=500,
            status_text="INTERNAL SERVER ERROR"
        )
        response.body = f"An unexpected error occurred: {str(e)}\nError Traceback: {format_exc()}\n"
        response.headers.set_single_value_header(
            name="Content-Type", value="text/plain"
        ).set_single_value_header(
            name="Content-Length", value=len(response.body)
        )
    return response
