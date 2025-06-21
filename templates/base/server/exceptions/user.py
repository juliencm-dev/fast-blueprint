from fastapi import status
from server.exceptions.base import ServerException

class UserNotFoundException(ServerException):
    pass

class UserWithEmailAlreadyExistsException(ServerException):
    pass

class UserNotVerifiedException(ServerException):
    pass

class UserRoleNotAllowedException(ServerException):
    pass

class UserNotCreatedException(ServerException):
    pass

class UserNotLoggedInException(ServerException):
    pass

USER_EXCEPTIONS = {
    UserNotFoundException: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "detail": {
            "message": "The user associated with the provided email or id was not found",
            "error_code": "user_not_found",
        },
    },
    UserWithEmailAlreadyExistsException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "The user associated with the provided email already exists",
            "error_code": "user_already_exists",
        },
    },
    UserNotVerifiedException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "The user associated with the provided email is not verified",
            "error_code": "user_not_verified",
        },
    },
    UserRoleNotAllowedException: {
        "status_code": status.HTTP_403_FORBIDDEN,
        "detail": {
            "message": "Only admins are allowed to access this route.",
            "error_code": "user_role_not_allowed",
        },
    },
    UserNotCreatedException: {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": {
            "message": "The user could not be created",
            "error_code": "user_not_created",
        },
    },
    UserNotLoggedInException: {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "detail": {
            "message": "There is currently no logged in user",
            "error_code": "user_not_logged_in",
        },
    },

}




