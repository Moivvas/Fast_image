from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, Tag
from src.services.auth import auth_service
from src.repository import tags as repo_tags
from src.schemas import TagModel, TagResponse
from src.conf import messages

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post('/', response_model=TagResponse)
async def create_tag(body: TagModel,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)) -> Tag | None:
    tag_exist = await repo_tags.get_tag_by_name(body.tag_name.lower(), db)
    if tag_exist:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.TAG_ALREADY_EXISTS)
    tag = await repo_tags.create_tag(body, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return tag


@router.get("/by_id/{tag_id}", response_model=TagResponse)
async def get_tag_by_id(tag_id: int,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)) -> Tag | None:
    tag = await repo_tags.get_tag_by_id(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.INVALID_TAG)
    return tag


@router.get("/by_name/{tag_name}", response_model=TagResponse)
async def get_tag_by_name(tag_name: str,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(auth_service.get_current_user)) -> Tag | None:
    tag = await repo_tags.get_tag_by_name(tag_name, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.INVALID_TAG)
    return tag


@router.get("/", response_model=List[TagResponse])
async def get_all_tags(db: Session = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)) -> List[Tag] | None:
    tags = await repo_tags.get_tags(db)
    return tags
    

@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: int,
                     body: TagModel,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)) -> Tag | None:
    tag = await repo_tags.update_tag(tag_id, body, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.INVALID_TAG)
    return tag


@router.delete("/", response_model=TagResponse)
async def delete_tag(identifier: str,
                     by_id: bool = False,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)) -> Tag | None:
    if by_id:
        tag = await repo_tags.remove_tag_by_id(int(identifier), db)
    else:
        tag = await repo_tags.remove_tag_by_name(identifier, db)

    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.INVALID_TAG)
    return tag
