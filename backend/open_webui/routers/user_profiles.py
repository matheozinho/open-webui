"""
User Profiles Router
API endpoints for managing user profiles in the UIMA system
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from open_webui.models.users import User
from open_webui.models.user_profiles import (
    UserProfiles,
    UserProfileForm,
    UserProfileModel,
)
from open_webui.routers.auths import get_current_user

router = APIRouter()


####################
# Routes
####################


@router.get("/profiles/user", response_model=UserProfileModel)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current user's profile
    """
    profile = UserProfiles.get_profile_by_user_id(current_user.id)
    
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile


@router.get("/profiles/user/{user_id}", response_model=UserProfileModel)
async def get_user_profile_by_id(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a user's profile by user ID (admin only)
    """
    # Check if current user is admin or requesting their own profile
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this profile"
        )
    
    profile = UserProfiles.get_profile_by_user_id(user_id)
    
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile


@router.post("/profiles/user", response_model=UserProfileModel)
async def create_user_profile(
    form_data: UserProfileForm,
    current_user: User = Depends(get_current_user)
):
    """
    Create or update the current user's profile
    """
    profile = UserProfiles.update_profile(current_user.id, form_data)
    
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create or update profile"
        )
    
    return profile


@router.put("/profiles/user", response_model=UserProfileModel)
async def update_user_profile(
    form_data: UserProfileForm,
    current_user: User = Depends(get_current_user)
):
    """
    Update the current user's profile
    """
    profile = UserProfiles.update_profile(current_user.id, form_data)
    
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )
    
    return profile


@router.delete("/profiles/user")
async def delete_user_profile(current_user: User = Depends(get_current_user)):
    """
    Delete the current user's profile
    """
    success = UserProfiles.delete_profile(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete profile"
        )
    
    return {"status": True}
