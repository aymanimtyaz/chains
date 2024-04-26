from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, IO
from typing_extensions import Self

from chains.src.request import IRequest, RequestV1_1
from chains.src.response import IResponse, ResponseV1_1
from chains.src.handlers import IBranchIngressHandler, BranchIngressHandlerV1_1, RootIngressHandlerV1_1
from chains.src.default_middlewares import root_error_handlerv1_1, catchall_error_handlerv1_1



class IBranch(ABC):

    @abstractmethod
    def route(self, path: str, method: str) -> Callable[[Callable[[IRequest], IResponse]], None]:
        pass

    @abstractmethod
    def add_branch(self, path: str, branch: IBranch) -> Self:
        pass

    @abstractmethod
    def middleware(self, *args, **kwargs) -> Callable[[Callable], None]:
        pass

    @property
    def _branch_ingress_handler(self) -> IBranchIngressHandler:
        pass

class BranchV1_1(IBranch):

    def __init__(self) -> None:
        self.__branch_ingress_handler: BranchIngressHandlerV1_1 = BranchIngressHandlerV1_1()

    def route(self, path: str, method: str) -> Callable[[Callable[[IRequest], IResponse]], None]:
        def decorator(route_function: Callable[[IRequest], IResponse]) -> None:
            self.__branch_ingress_handler.branch_handler.add_route(
                path=path,
                method=method,
                route_function=route_function
            )
            return None
        return decorator

    def add_branch(self, path: str, branch: IBranch) -> Self:
        self._branch_ingress_handler.branch_handler.add_branch(
            name=path,
            branch_ingress_handler=branch._branch_ingress_handler
        )
        return self

    def middleware(self, *args, **kwargs) -> Callable[[Callable], None]:
        def decorator(middleware_function) -> None:
            self._branch_ingress_handler.add_middleware(
                middleware_function,
                *args,
                **kwargs
            )
        return decorator

    @property
    def _branch_ingress_handler(self) -> BranchIngressHandlerV1_1:
        return self.__branch_ingress_handler

    def __str__(self) -> str:
        return str(self.__branch_ingress_handler)



class IApp(IBranch, ABC):

    @abstractmethod
    def handle_request(self, request: IRequest) -> IResponse:
        pass

class AppV1_1(BranchV1_1, IApp):

    def __init__(self) -> None:
        super().__init__()
        self.__root_ingress_handler: RootIngressHandlerV1_1 = RootIngressHandlerV1_1(
            primary_branch_ingress_handler=self._branch_ingress_handler
        )
        self.__root_ingress_handler.primary_branch_ingress_handler.add_middleware(
            middleware_function=root_error_handlerv1_1
        )
        self.__root_ingress_handler.add_middleware(
            middleware_function=catchall_error_handlerv1_1
        )

    def handle_request(self, request: RequestV1_1) -> ResponseV1_1:
        return self.__root_ingress_handler.handle(
            request=request
        )



class IWSGIApp(IApp, ABC):

    @abstractmethod
    def __call__(self, environ: dict[str, str|list[str]|IO], start_response: Callable[[str, list[tuple[str, str]]], Any]) -> Iterable[bytes]:
        pass

class WSGIAppV1_1(AppV1_1, IWSGIApp):

    def __init__(self) -> None:
        super().__init__()

    def __call__(self, environ: dict[str, str|list[str]|IO], start_response: Callable[[str, list[tuple[str, str]]], Any]) -> Iterable[bytes]:
        path, method = environ["PATH_INFO"], environ["REQUEST_METHOD"]
        request: Request = Request(
            method=method,
            path=path
        )
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                if key == "HTTP_COOKIE":
                    request.headers.set_single_value_header(
                        name="Cookie", value=value
                    )
                else:
                    header_name: str = key[5:]
                    header_values: list[str] = value.split(",")
                    if len(header_values) > 1:
                        for val in header_values:
                            request.headers.add_multi_value_header(
                                name=header_name, value=val.strip()
                            )
                    else:
                        request.headers.set_single_value_header(
                            name=header_name, value=value
                        )
            elif key == "wsgi.input":
                body: bytes = value.read()
                if len(body) > 0:
                    request.body = body

        response: Response = self.handle_request(
            request=request
        )

        status: str = f"{response.status_code} {response.status_text}"
        headers: list[tuple[str, str]] = list()
        for key, value in request.headers.yield_all_headers():
            headers.append((key, str(value)))

        start_response(status, headers)
        response_body: bytes = response.body if response.body is not None else b""
        return [response_body]



Chains = WSGIAppV1_1
Branch = BranchV1_1
Request = RequestV1_1
Response = ResponseV1_1
