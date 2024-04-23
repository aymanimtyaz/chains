from abc import ABC



class ChainsBaseException(Exception, ABC):
    pass


class ChainsHTTPException(ChainsBaseException, ABC):
    pass

class NotFoundException(ChainsHTTPException):

    def __init__(self) -> None:
        super().__init__("The specified path does not exist")

class MethodNotAllowedException(ChainsHTTPException):

    def __init__(self, allowed_methods: list[str]) -> None:
        self.allowed_methods: list[str] = allowed_methods
        super().__init__(
            "The resource was found but it does not support the specified method. "
            "Check the 'Allow' header for a list of supported methods."
        )
