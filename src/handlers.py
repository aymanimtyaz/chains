from __future__ import annotations

from typing import Callable
from typing_extensions import Self
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from chains.src.request import IRequest
from chains.src.response import IResponse
from chains.src.exceptions import NotFoundException, MethodNotAllowedException



class IRequestHandler(ABC):

    @abstractmethod
    def handle(self, request: IRequest) -> IResponse:
        pass



class IMiddlewareHandler(IRequestHandler, ABC):

    @property
    @abstractmethod
    def next(self) -> IMiddlewareHandler|IBranchHandler|IBranchIngressHandler:
        pass

    @next.setter
    @abstractmethod
    def next(self, next: IMiddlewareHandler|IBranchHandler|IBranchIngressHandler) -> Self:
        pass



class IIngressHandler(IRequestHandler, ABC):

    def add_middleware(self, middleware_function: Callable[[IRequest, Callable[[IRequest], IResponse]], IResponse]) -> Self:
        middleware: MiddlewareHandlerV1_1 = MiddlewareHandlerV1_1(
            next=self._next,
            middleware_function=middleware_function
        )
        self._next = middleware
        return self

class IRootIngressHandler(IIngressHandler, ABC):

    @property
    @abstractmethod
    def primary_branch_ingress_handler(self) -> IBranchIngressHandler:
        pass

    @property
    def next(self) -> IMiddlewareHandler|IBranchIngressHandler:
        pass

class IBranchIngressHandler(IIngressHandler, ABC):

    @property
    @abstractmethod
    def next(self) -> IBranchHandler|IMiddlewareHandler:
        pass

    @property
    @abstractmethod
    def branch_handler(self) -> IBranchHandler:
        pass



class IRouteHandler(IRequestHandler, ABC):

    @property
    @abstractmethod
    def route_function(self) -> Callable[[IRequest], IResponse]:
        pass



class IBranchHandler(IRequestHandler, ABC):

    @abstractmethod
    def add_branch(self, name: str, branch_ingress_handler: IBranchIngressHandler) -> Self:
        pass

    @abstractmethod
    def add_route(self, path: str, method: str, route_function: Callable[[IRequest], IResponse]) -> Self:
        pass



class RootIngressHandlerV1_1(IRootIngressHandler):

    def __init__(self, primary_branch_ingress_handler: IBranchIngressHandler) -> None:
        self._primary_branch_ingress_handler: IBranchIngressHandler = primary_branch_ingress_handler
        self._next: IMiddlewareHandler|IBranchIngressHandler = self._primary_branch_ingress_handler

    @property
    def primary_branch_ingress_handler(self) -> IBranchIngressHandler:
        return self._primary_branch_ingress_handler

    @property
    def next(self) -> IMiddlewareHandler|IBranchIngressHandler:
        return self._next

    def handle(self, request: IRequest) -> IResponse:
        return self._next.handle(
            request=request
        )

class BranchIngressHandlerV1_1(IBranchIngressHandler):

    def __init__(self) -> None:
        self._branch_handler: BranchHandlerV1_1 = BranchHandlerV1_1()
        self._next: BranchHandlerV1_1|IMiddlewareHandler = self._branch_handler

    @property
    def next(self) -> BranchHandlerV1_1|IMiddlewareHandler:
        return self._next

    @property
    def branch_handler(self) -> BranchHandlerV1_1:
        return self._branch_handler

    def handle(self, request: IRequest) -> IResponse:
        return self._next.handle(
            request=request
        )

    def __str__(self) -> str:
        return self._str_helper_()

    def _str_helper_(self, indentation: int = 0) -> str:
        tab: str = "\t"
        s: str = ""
        bh: BranchHandlerV1_1 = self.branch_handler
        for branch_name, branch_ingress_handler in bh._branches.items():
            s += f"{tab*indentation}path: /{branch_name}\n"
            s += branch_ingress_handler._str_helper_(indentation=indentation+1) + "\n"
        s += bh._routes._str_helper_(indentation=indentation) + "\n"
        return s



class MiddlewareHandlerV1_1(IMiddlewareHandler):

    def __init__(self, next: IMiddlewareHandler|IBranchHandler|IBranchIngressHandler, middleware_function: Callable[[IRequest, Callable[[IRequest], IResponse]], IResponse]) -> None:
        self._next: IMiddlewareHandler|IBranchHandler|IBranchIngressHandler = next
        self._middleware_function: Callable[[IRequest, Callable[[IRequest], IResponse]], IResponse] = middleware_function

        def wrapped_next(request: IRequest) -> IResponse:
            return self._next.handle(
                request=request
            )
        self._wrapped_next: Callable[[IRequest], IResponse] = wrapped_next

    @property
    def next(self) -> IMiddlewareHandler|IBranchHandler|IBranchIngressHandler:
        if self._next is None:
            #TODO: Raise a proper error here
            raise ValueError("The downstream handler for this middleware hasn't been set")
        return self._next

    @next.setter
    def next(self, next: IMiddlewareHandler|IBranchHandler|IBranchIngressHandler) -> Self:
        self._next = next
        def wrapped_next(request: IRequest) -> IResponse:
            return self._next.handle(
                request=request
            )
        self._wrapped_next = wrapped_next
        return self

    def handle(self, request: IRequest) -> IResponse:
        return self._middleware_function(request, self._wrapped_next)



class RouteHandlerV1_1(IRouteHandler):

    def __init__(self, route_function: Callable[[IRequest], IResponse]) -> None:
        self._route_function: Callable[[IRequest], IResponse] = route_function

    @property
    def route_function(self) -> Callable[[IRequest], IResponse]:
        return self._route_function

    def handle(self, request: IRequest) -> IResponse:
        return self._route_function(request)

    def __str__(self) -> str:
        return f"{self._route_function.__name__}()"



class RouteTableEntry:

    def __init__(self) -> None:
        self._route_table: RouteTable|None = None
        self._route_handlers: dict[str, IRouteHandler] = dict()

    @property
    def route_table(self) -> RouteTable:
        if self._route_table is None:
            raise NotFoundException()
        return self._route_table

    @route_table.setter
    def route_table(self, route_table: RouteTable) -> Self:
        if self._route_table is not None:
            #TODO: Raise an appropriate error
            raise ValueError("RouteTable has already been set")
        self._route_table = route_table
        return self

    def get_route_handler_for_method(self, method: str) -> IRouteHandler:
        if method not in self._route_handlers:
            raise MethodNotAllowedException(
                allowed_methods=list(self._route_handlers.keys())
            )
        return self._route_handlers[method]

    def add_route_handler_for_method(self, method: str, route_handler: IRouteHandler) -> Self:
        if method in self._route_handlers:
            #TODO: Raise appropriate error
            raise ValueError("That route has already been registered")
        self._route_handlers[method] = route_handler
        return self

class RouteTable:

    def __init__(self):
        self._table: dict[str, RouteTableEntry] = dict()
        self._wildcard: RouteTableEntry = RouteTableEntry()
        self._wildcard_ingress_allowed: bool = False

    def __preprocess_path(self, path: str) -> str:
        return path.lstrip().lstrip("/").rstrip("/")

    def check_for_branch_collision(self, branch_name: str) -> bool:
        preprocessed_branch_name: str = self.__preprocess_path(
            path=branch_name
        )
        if preprocessed_branch_name in self._table:
            return True
        return False

    def __str__(self) -> str:
        return self._str_helper_()

    def _str_helper_(self, indentation: int = 0) -> str:
        tab: str = "\t"
        s: str = ""
        for path, round_table_entry in self._table.items():
            s += f"{tab*indentation}path: /{path}\n"
            for method, route_handler in round_table_entry._route_handlers.items():
                s += f"{tab*(indentation+1)}handler: {method}: {route_handler}\n"
            try:
                s += round_table_entry.route_table._str_helper_(indentation=indentation+1)
            except:
                pass
        wildcard_printed: bool = False
        if len(self._wildcard._route_handlers) > 0:
            s += f"{tab*indentation}path: /<>\n"
            wildcard_printed = True
        for method, route_handler in self._wildcard._route_handlers.items():
            s += f"{tab*(indentation+1)}handler: {method}: {route_handler}\n"
        try:
            wildcard_route_table: RouteTable = self._wildcard.route_table
        except:
            pass
        else:
            if not wildcard_printed:
                s += f"{tab*indentation}path: /<>\n"
            s += wildcard_route_table._str_helper_(indentation=indentation+1)
        return s

    def add_path(self, path: str, method: str, route_handler: IRouteHandler) -> Self:
        preprocessed_path: str = self.__preprocess_path(
            path=path
        )
        current_path_characters: list[str] = list()
        for char in preprocessed_path:
            if char == "/":
                break
            current_path_characters.append(char)
        current_path: str = "".join(current_path_characters)
        path_remnant: str = preprocessed_path.lstrip(current_path)
        if current_path == "<>":
            if len(path_remnant) > 0:
                self._wildcard.route_table = RouteTable()
                self._wildcard.route_table.add_path(
                    path=path_remnant,
                    method=method,
                    route_handler=route_handler
                )
            else:
                self._wildcard.add_route_handler_for_method(
                    method=method,
                    route_handler=route_handler
                )
                self._wildcard_ingress_allowed = True
        else:
            if current_path in self._table:
                if len(path_remnant) > 0:
                    try:
                        route_table: RouteTable = self._table[current_path].route_table
                    except:
                        self._table[current_path].route_table = RouteTable()
                        route_table: RouteTable = self._table[current_path].route_table
                    route_table.add_path(
                        path=path_remnant,
                        method=method,
                        route_handler=route_handler
                    )
                else:
                    self._table[current_path].add_route_handler_for_method(
                        method=method,
                        route_handler=route_handler
                    )
            else:
                self._table[current_path] = RouteTableEntry()
                self._table[current_path].route_table = RouteTable()
                if len(path_remnant) > 0:
                    self._table[current_path].route_table.add_path(
                        path=path_remnant,
                        method=method,
                        route_handler=route_handler
                    )
                else:
                    self._table[current_path].add_route_handler_for_method(
                        method=method,
                        route_handler=route_handler
                    )
        return self

    def get_route(self, path: str, method: str) -> IRouteHandler:
        preprocessed_path: str = self.__preprocess_path(
            path=path
        )
        current_path_characters: list[str] = list()
        for char in preprocessed_path:
            if char == "/":
                break
            current_path_characters.append(char)
        current_path: str = "".join(current_path_characters)
        path_remnant: str = preprocessed_path.lstrip(current_path)
        if current_path in self._table:
            if len(path_remnant) > 0:
                return self._table[current_path].route_table.get_route(
                    path=path_remnant,
                    method=method
                )
            else:
                return self._table[current_path].get_route_handler_for_method(
                    method=method
                )
        else:
            if len(path_remnant) > 0:
                return self._wildcard.route_table.get_route(
                    path=path_remnant,
                    method=method
                )
            else:
                if self._wildcard_ingress_allowed is True:
                    return self._wildcard.get_route_handler_for_method(
                        method=method
                    )
                else:
                    raise NotFoundException()

class BranchHandlerV1_1(IBranchHandler):

    def __init__(self) -> None:
        self._branches: dict[str, BranchIngressHandlerV1_1] = dict()
        self._routes: RouteTable = RouteTable()

    def __preprocess_path(self, path: str) -> str:
        return path.lstrip().lstrip("/").rstrip("/")

    def add_branch(self, name: str, branch_ingress_handler: IBranchIngressHandler) -> Self:
        preprocessed_name: str = self.__preprocess_path(
            path=name
        )
        if len(preprocessed_name) < 1:
            raise ValueError("Can not create a branch with name '/'")
        if "/" in preprocessed_name:
            raise ValueError(
                "Malformed branch name, name should not contain any forward slashes apart from the optional leading one."
            )
        if preprocessed_name in self._branches:
            raise ValueError("A branch with the same path already exists")
        if self._routes.check_for_branch_collision(branch_name=preprocessed_name):
            raise ValueError(
                "A route exists off of this branch with the same prefix as the branch you're trying to add."
            )
        self._branches[preprocessed_name] = branch_ingress_handler
        return Self

    def add_route(self, path: str, method: str, route_function: Callable[[IRequest], IResponse]) -> Self:
        preprocessed_path: str = self.__preprocess_path(
            path=path
        )
        path_prefix_characters: list[str] = list()
        for char in preprocessed_path:
            if char == "/":
                break
            path_prefix_characters.append(char)
        path_prefix: str = "".join(path_prefix_characters)
        if path_prefix in self._branches:
            raise ValueError(
                "A branch exists off of this route with the same path as the prefix of the route you're trying to add."
            )
        new_route_handler: RouteHandlerV1_1 = RouteHandlerV1_1(
            route_function=route_function
        )
        self._routes.add_path(
            path=path,
            method=method,
            route_handler=new_route_handler
        )
        return self

    def handle(self, request: IRequest) -> IResponse:
        path, method = request.path, request.method
        parsed_path: str = urlparse(path).path
        preprocessed_path: str = self.__preprocess_path(
            path=parsed_path
        )
        path_prefix_characters: list[str] = list()
        for char in preprocessed_path:
            if char == "/":
                break
            path_prefix_characters.append(char)
        path_prefix: str = "".join(path_prefix_characters)
        path_remnant: str = preprocessed_path.lstrip(path_prefix)
        if path_prefix in self._branches:
            branch_ingress_handler: IBranchIngressHandler = self._branches[path_prefix]
            request.path = path_remnant
            return branch_ingress_handler.handle(
                request=request
            )
        else:
            route_handler: IRouteHandler = self._routes.get_route(
                path=preprocessed_path,
                method=method
            )
            return route_handler.handle(
                request=request
            )
