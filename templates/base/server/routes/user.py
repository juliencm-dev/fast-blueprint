from typing import List

from fastapi import APIRouter, Depends, Request, status

from server.db.user.schema import User
from server.exceptions.user import UserNotFoundException
from server.services.auth.dependencies import get_current_active_user
from server.services.user import get_user_service
from server.models import UserResponse, UserUpdateRequest 
from server.services.user.service import UserService

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(user_service: UserService = Depends(get_user_service) , current_user: User = Depends(get_current_active_user)):
    """Get all users. Returns a list of users."""
    return await user_service.get_users(current_user)
    
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get the current user. Returns the user associated to the current session."""
    return current_user

@router.get("/{userd_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(userd_id: str, user_service: UserService = Depends(get_user_service) , current_user: User = Depends(get_current_active_user)):
    """Get a user by id. Returns the user associated to the provided id."""
    user = await user_service.get_user(userd_id, current_user)
    if not user:
        raise UserNotFoundException()
    return user

@router.patch("/{userd_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(userd_id: str, user_data: UserUpdateRequest, user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_active_user)):
    """Update a user by id. Returns the updated user."""
    return await user_service.update_user(userd_id, user_data, current_user)

@router.delete("/{userd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(userd_id: str, user_service: UserService = Depends(get_user_service), current_user: User = Depends(get_current_active_user)):
    """Delete a user by id."""
    await user_service.delete_user(userd_id, current_user)
    
