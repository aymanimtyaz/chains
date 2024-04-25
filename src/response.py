from typing_extensions import Self
from abc import ABC, abstractmethod

from chains.src.header import IHeaders, HeadersV1_1



class IResponse(ABC):

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
    def body(self) -> bytes|None:
        pass

    @body.setter
    @abstractmethod
    def body(self, body: bytes) -> Self:
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
        self._body: bytes|None = None

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
    def body(self) -> bytes|None:
        return self._body

    @body.setter
    def body(self, body: bytes) -> Self:
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
