from fastapi import HTTPException


def bad_request(detail: str = "Bad request") -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=401, detail=detail)


def not_found(detail: str = "Not found") -> HTTPException:
    return HTTPException(status_code=404, detail=detail)


def conflict(detail: str = "Conflict") -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def forbidden(detail: str = "Forbidden") -> HTTPException:
    return HTTPException(status_code=403, detail=detail)


def service_unavailable(detail: str = "Service unavailable") -> HTTPException:
    return HTTPException(status_code=503, detail=detail)
