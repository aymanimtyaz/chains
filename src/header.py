from typing_extensions import Self
from typing import Generator
from abc import ABC, abstractmethod



class IHeaders(ABC):

    @abstractmethod
    def get_single_value_header(self, name: str) -> str|None:
        pass

    @abstractmethod
    def set_single_value_header(self, name: str, value: str) -> Self:
        pass

    @abstractmethod
    def delete_single_value_header(self, name: str) -> Self:
        pass

    @abstractmethod
    def add_multi_value_header(self, name: str, value: str) -> Self:
        pass

    @abstractmethod
    def yield_multi_value_header(self, name: str) -> Generator[str, str, None]:
        pass

    @abstractmethod
    def delete_multi_value_header(self, name: str) -> Self:
        pass

    @abstractmethod
    def yield_all_headers(self) -> Generator[tuple[str, str], None, None]:
        pass

    @abstractmethod
    def serialize(self) -> str:
        pass



class HeadersV1_1(IHeaders):

    def __init__(self) -> None:
        self._single_value_headers: dict[str, str] = dict()
        self._multi_value_headers: dict[str, list[str]] = dict()

    def set_single_value_header(self, name: str, value: str) -> Self:
        if name in self._multi_value_headers:
            #TODO: Add an exception for a header clash
            raise ValueError("Multi value headers with the same name already exists")
        self._single_value_headers[name] = value
        return self

    def get_single_value_header(self, name: str) -> str|None:
        if name not in self._single_value_headers:
            return None
        return self._single_value_headers[name]

    def delete_single_value_header(self, name: str) -> Self:
        if name in self._single_value_headers:
            del self._single_value_headers[name]
        return self

    def add_multi_value_header(self, name: str, value: str) -> Self:
        if name in self._single_value_headers:
            #TODO: Add an exception for a header clash
            raise ValueError("A single value header with the same name already exists")
        if name not in self._multi_value_headers:
            self._multi_value_headers[name] = list()
        self._multi_value_headers[name].append(value)
        return self

    def yield_multi_value_header(self, name: str) -> Generator[str, str, None]:
        if name in self._multi_value_headers:
            for header_value in self._multi_value_headers[name]:
                yield header_value
        return None

    def delete_multi_value_header(self, name: str) -> Self:
        if name in self._multi_value_headers:
            del self._multi_value_headers[name]
        return self

    def yield_all_headers(self) -> Generator[tuple[str, str], None, None]:
        for header_name, header_value in self._single_value_headers.items():
            yield (header_name, header_value)
        for header_name, header_values in self._multi_value_headers.items():
            for header_value in header_values:
                yield (header_name, header_value)
        return None

    def serialize(self) -> str:
        headers_list: list[str] = list()
        for header_name, header_value in self.yield_all_headers():
            headers_list.append(f"{header_name}: {header_value}\r\n")
        return "".join(headers_list)
