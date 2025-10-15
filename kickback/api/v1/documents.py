from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from kickback.api import deps
from kickback.domain import schemas
from kickback.services.documents import DocumentConflictError, DocumentNotFoundError, DocumentService


router = APIRouter(dependencies=[Depends(deps.enforce_rate_limit)])


@router.post("/documents", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: schemas.DocumentCreate,
    service: DocumentService = Depends(deps.get_document_service),
) -> schemas.DocumentRead:
    try:
        return await service.create_document(payload)
    except DocumentConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document already exists")


@router.get("/documents/{document_id}", response_model=schemas.DocumentRead)
async def get_document(
    document_id: int,
    service: DocumentService = Depends(deps.get_document_service),
) -> schemas.DocumentRead:
    try:
        return await service.get_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
