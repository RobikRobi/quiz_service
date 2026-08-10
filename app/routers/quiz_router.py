import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.dependencies import get_current_user_id
from app.schemas.quiz import (
    AttemptCreate,
    AttemptRead,
    QuizCreate,
    QuizRead,
    QuizUpdate,
)
from app.services.quiz_service import (
    create_quiz,
    delete_quiz,
    get_attempt,
    get_quiz,
    list_my_quizzes,
    publish_quiz,
    submit_attempt,
    update_quiz,
)

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]


@router.post("/quizzes", response_model=QuizRead)
async def create_quiz_endpoint(
    data: QuizCreate,
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    return await create_quiz(data, current_user_id, session)


@router.get("/quizzes", response_model=list[QuizRead])
async def list_quizzes_endpoint(
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    return await list_my_quizzes(current_user_id, session)


@router.get("/quizzes/{quiz_id}", response_model=QuizRead)
async def get_quiz_endpoint(
    quiz_id: uuid.UUID,
    session: SessionDep,
):
    return await get_quiz(quiz_id, session)


@router.put("/quizzes/{quiz_id}", response_model=QuizRead)
async def update_quiz_endpoint(
    quiz_id: uuid.UUID,
    data: QuizUpdate,
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    return await update_quiz(quiz_id, data, current_user_id, session)


@router.post("/quizzes/{quiz_id}/publish", response_model=QuizRead)
async def publish_quiz_endpoint(
    quiz_id: uuid.UUID,
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    return await publish_quiz(quiz_id, current_user_id, session)


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz_endpoint(
    quiz_id: uuid.UUID,
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    await delete_quiz(quiz_id, current_user_id, session)
    return {"success": True, "message": "Quiz deleted"}


@router.post("/quizzes/{quiz_id}/attempts", response_model=AttemptRead)
async def submit_attempt_endpoint(
    quiz_id: uuid.UUID,
    data: AttemptCreate,
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    return await submit_attempt(quiz_id, data, current_user_id, session)


@router.get("/attempts/{attempt_id}", response_model=AttemptRead)
async def get_attempt_endpoint(
    attempt_id: uuid.UUID,
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
):
    return await get_attempt(attempt_id, current_user_id, session)
