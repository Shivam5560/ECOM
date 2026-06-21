class AppError(Exception):
    code = "app_error"
    status_code = 500

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppError):
    code = "validation_error"
    status_code = 422


class UnauthorizedError(AppError):
    code = "unauthorized"
    status_code = 401


class ForbiddenError(AppError):
    code = "forbidden"
    status_code = 403


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404


class ServiceUnavailableError(AppError):
    code = "service_unavailable"
    status_code = 503

    def __init__(self, service_name: str, message: str = "service unavailable") -> None:
        self.service_name = service_name
        super().__init__(message, status_code=self.status_code)


class ServiceCallError(AppError):
    code = "service_call_error"

    def __init__(self, service_name: str, message: str, *, status_code: int = 502) -> None:
        self.service_name = service_name
        super().__init__(message, status_code=status_code)
