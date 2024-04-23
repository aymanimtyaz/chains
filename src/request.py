from typing_extensions import Self
from abc import ABC, abstractmethod

from chains.src.header import IHeaders, HeadersV1_1



class IRequest(ABC):

    @abstractmethod
    def serialize(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, text: str) -> Self:
        pass

    @property
    @abstractmethod
    def method(self) -> str:
        pass

    @method.setter
    @abstractmethod
    def method(self, method: str) -> Self:
        pass

    @property
    @abstractmethod
    def path(self) -> str:
        pass

    @path.setter
    @abstractmethod
    def path(self, path: str) -> Self:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def headers(self) -> IHeaders:
        pass

    @property
    @abstractmethod
    def body(self) -> str|None:
        pass

    @body.setter
    @abstractmethod
    def body(self, body: str) -> Self:
        pass

    @body.deleter
    @abstractmethod
    def body(self) -> Self:
        pass



class RequestV1_1(IRequest):

    __VERSION: str = "1.1"

    def __init__(
        self,
        method: str,
        path: str,
    ):
        self._method: str = method
        self._path: str = path
        self._headers: HeadersV1_1 = HeadersV1_1()
        self._body: str|None = None

    def _serialize_request_line(self) -> str:
        return f"{self._method} {self._path} HTTP/{self.__VERSION}\r\n"

    def serialize(self) -> str:
        serialization_components: list[str] = [
            self._serialize_request_line()
        ]
        serialized_headers: str = self._headers.serialize()
        if len(serialized_headers) > 1:
            serialization_components.append(serialized_headers)
        serialization_components.append("\r\n")
        if self._body is not None:
            serialization_components.append(self._body)
        return "".join(serialization_components)

    @classmethod
    def deserialize(cls, text: str) -> Self:
        split_lines: list[str] = text.split("\r\n")
        request_line: str = split_lines[0]
        headers: list[str] = split_lines[1:-1][:-1]
        body: str = split_lines[-1]

        req_line_components: list[str] = request_line.split(" ")
        method: str = req_line_components[0]
        path: str = req_line_components[1]

        new_request: Self = cls(
            method=method,
            path=path
        )

        single_value_headers: dict[str, str] = dict()
        multi_value_headers: dict[str, list[str]] = dict()
        for header_line in headers:
            header_components: list[str] = header_line.split(":")
            header_name: str = header_components[0].strip()
            header_value: str = header_components[1].strip()
            if header_name in single_value_headers:
                multi_value_headers[header_name] = [
                    single_value_headers[header_name],
                    header_value
                ]
            elif header_name in multi_value_headers:
                multi_value_headers[header_name].append(
                    header_value
                )
            else:
                single_value_headers[header_name] = header_value

        for header_name, header_value in single_value_headers.items():
            new_request.headers.set_single_value_header(
                name=header_name,
                value=header_value
            )

        for header_name, header_values in multi_value_headers.items():
            for header_value in header_values:
                new_request.headers.add_multi_value_header(
                    name=header_name,
                    value=header_value
                )

        if len(body) > 0:
            new_request.body = body

        return new_request

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, method: str) -> Self:
        self._method = method
        return self

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> Self:
        self._path = path
        return self

    @property
    def version(self) -> str:
        return self.__VERSION

    @property
    def headers(self) -> HeadersV1_1:
        return self._headers

    @property
    def body(self) -> str|None:
        return self._body

    @body.setter
    def body(self, body: str) -> Self:
        if len(body) < 1:
            #TODO: Add an exception for a zero length body
            raise ValueError("The body has to have a minimum size/length of 1 byte")
        self._body = body
        return self

    @body.deleter
    def body(self) -> Self:
        if not self._body:
            #TODO: Add an exception for a non existant body
            raise ValueError("The body does not exist/ has not been set")
        self._body = None
        return self

    def __str__(self) -> str:
        return self.serialize()
