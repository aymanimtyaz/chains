from typing_extensions import Self
from abc import ABC, abstractmethod

from chains.src.header import IHeaders, HeadersV1_1



class IRequest(ABC):

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
        self._body: bytes|None = None

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
