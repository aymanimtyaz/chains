from typing_extensions import Self
from abc import ABC, abstractmethod

from chains.src.header import IHeaders, HeadersV1_1



class IResponse(ABC):

    @abstractmethod
    def serialize(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, text: str) -> Self:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def status_code(self) -> int:
        pass

    @status_code.setter
    @abstractmethod
    def status_code(self, code: int) -> Self:
        pass

    @property
    @abstractmethod
    def status_text(self) -> str:
        pass

    @status_text.setter
    @abstractmethod
    def status_text(self, text: str) -> Self:
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



class ResponseV1_1(IResponse):

    __VERSION: str = "1.1"

    def __init__(
        self,
        status_code: int,
        status_text: str
    ) -> None:
        self._status_code: int = status_code
        self._status_text: str = status_text
        self._headers: HeadersV1_1 = HeadersV1_1()
        self._body: str|None = None

    def _serialize_response_line(self) -> str:
        return f"HTTP/{self.__VERSION} {self._status_code} {self._status_text}\r\n"

    def serialize(self) -> str:
        serialization_components: list[str] = [
            self._serialize_response_line()
        ]
        serialized_headers: str = self._headers.serialize()
        if len(serialized_headers) > 0:
            serialization_components.append(serialized_headers)
        serialization_components.append("\r\n")
        if self._body is not None:
            serialization_components.append(self._body)
        return "".join(serialization_components)

    @classmethod
    def deserialize(cls, text: str) -> Self:
        components: list[str] = text.split("\r\n")
        response_line: str = components[0]
        headers: list[str] = components[1:-1][:-1]
        body: str = components[-1]

        response_line_components: list[str] = response_line.split(" ")
        status_code: int = int(response_line_components[1])
        status_text: str = response_line_components[2]

        new_response: Self = cls(
            status_code=status_code,
            status_text=status_text
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
            new_response.headers.set_single_value_header(
                name=header_name,
                value=header_value
            )

        for header_name, header_values in multi_value_headers.items():
            for header_value in header_values:
                new_response.headers.add_multi_value_header(
                    name=header_name,
                    value=header_value
                )

        if len(body) > 0:
            new_response.body = body

        return new_response


    @property
    def version(self) -> str:
        return self.__VERSION

    @property
    def status_code(self) -> int:
        return self._status_code

    @status_code.setter
    def status_code(self, code: int) -> Self:
        self._status_code = code
        return self

    @property
    def status_text(self) -> str:
        return self._status_text

    @status_text.setter
    def status_text(self, text: str) -> Self:
        self._status_text = text
        return self

    @property
    def headers(self) -> HeadersV1_1:
        return self._headers

    @property
    def body(self) -> str|None:
        return self._body

    @body.setter
    def body(self, body: str) -> Self:
        self._body = body
        return self

    @body.deleter
    def body(self) -> Self:
        self._body = None
        return self

    def __str__(self) -> str:
        return self.serialize()
