import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import QuestionType, QuizStatus
from app.models.answer_option import AnswerOption
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.schemas.quiz import AttemptCreate, QuestionCreate, QuizCreate, QuizUpdate


def _quiz_options():
    return selectinload(Quiz.questions).selectinload(Question.options)


async def _get_quiz_or_404(quiz_id: uuid.UUID, session: AsyncSession) -> Quiz:
    result = await session.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id)
        .options(_quiz_options())
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


def _ensure_owner(quiz: Quiz, user_id: uuid.UUID) -> None:
    if quiz.owner_user_id != user_id:
        raise HTTPException(status_code=403, detail="Only quiz owner can perform this action")


def _build_questions(items: list[QuestionCreate]) -> list[Question]:
    questions: list[Question] = []
    for index, item in enumerate(items):
        question = Question(
            text=item.text,
            question_type=item.question_type,
            position=item.position or index,
            points=item.points,
            accepted_answers=item.accepted_answers,
            options=[
                AnswerOption(
                    text=option.text,
                    is_correct=option.is_correct,
                    position=option.position or option_index,
                )
                for option_index, option in enumerate(item.options)
            ],
        )
        questions.append(question)
    return questions


async def create_quiz(data: QuizCreate, owner_user_id: uuid.UUID, session: AsyncSession) -> Quiz:
    quiz = Quiz(
        owner_user_id=owner_user_id,
        title=data.title,
        description=data.description,
        questions=_build_questions(data.questions),
    )
    session.add(quiz)
    await session.flush()
    return await _get_quiz_or_404(quiz.id, session)


async def list_my_quizzes(owner_user_id: uuid.UUID, session: AsyncSession) -> list[Quiz]:
    result = await session.execute(
        select(Quiz)
        .where(Quiz.owner_user_id == owner_user_id)
        .options(_quiz_options())
        .order_by(Quiz.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def get_quiz(quiz_id: uuid.UUID, session: AsyncSession) -> Quiz:
    return await _get_quiz_or_404(quiz_id, session)


async def update_quiz(
    quiz_id: uuid.UUID,
    data: QuizUpdate,
    owner_user_id: uuid.UUID,
    session: AsyncSession,
) -> Quiz:
    quiz = await _get_quiz_or_404(quiz_id, session)
    _ensure_owner(quiz, owner_user_id)

    if data.title is not None:
        quiz.title = data.title
    if data.description is not None:
        quiz.description = data.description
    if data.status is not None:
        quiz.status = data.status
    if data.questions is not None:
        quiz.questions = _build_questions(data.questions)

    await session.flush()
    return await _get_quiz_or_404(quiz.id, session)


async def publish_quiz(quiz_id: uuid.UUID, owner_user_id: uuid.UUID, session: AsyncSession) -> Quiz:
    quiz = await _get_quiz_or_404(quiz_id, session)
    _ensure_owner(quiz, owner_user_id)
    if not quiz.questions:
        raise HTTPException(status_code=400, detail="Quiz must have at least one question")
    quiz.status = QuizStatus.PUBLISHED
    await session.flush()
    return await _get_quiz_or_404(quiz.id, session)


async def delete_quiz(quiz_id: uuid.UUID, owner_user_id: uuid.UUID, session: AsyncSession) -> None:
    quiz = await _get_quiz_or_404(quiz_id, session)
    _ensure_owner(quiz, owner_user_id)
    await session.delete(quiz)


def _grade_question(question: Question, answer) -> tuple[bool, int]:
    if question.question_type == QuestionType.TEXT:
        accepted = {value.strip().lower() for value in question.accepted_answers or []}
        submitted = (answer.text_answer or "").strip().lower()
        is_correct = bool(submitted) and submitted in accepted
        return is_correct, question.points if is_correct else 0

    correct_ids = {str(option.id) for option in question.options if option.is_correct}
    selected_ids = {str(option_id) for option_id in answer.selected_option_ids or []}
    is_correct = selected_ids == correct_ids
    return is_correct, question.points if is_correct else 0


async def submit_attempt(
    quiz_id: uuid.UUID,
    data: AttemptCreate,
    student_user_id: uuid.UUID,
    session: AsyncSession,
) -> QuizAttempt:
    quiz = await _get_quiz_or_404(quiz_id, session)
    if quiz.status != QuizStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Quiz is not published")

    answers_by_question_id = {answer.question_id: answer for answer in data.answers}
    max_score = sum(question.points for question in quiz.questions)
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_user_id=student_user_id,
        max_score=max_score,
        score=0,
    )

    score = 0
    for question in quiz.questions:
        answer = answers_by_question_id.get(question.id)
        if not answer:
            is_correct = False
            points_awarded = 0
            selected_option_ids = None
            text_answer = None
        else:
            is_correct, points_awarded = _grade_question(question, answer)
            selected_option_ids = [str(option_id) for option_id in answer.selected_option_ids or []] or None
            text_answer = answer.text_answer

        score += points_awarded
        attempt.answers.append(
            AttemptAnswer(
                question_id=question.id,
                selected_option_ids=selected_option_ids,
                text_answer=text_answer,
                is_correct=is_correct,
                points_awarded=points_awarded,
            )
        )

    attempt.score = score
    session.add(attempt)
    await session.flush()
    return await get_attempt(attempt.id, student_user_id, session)


async def get_attempt(
    attempt_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession,
) -> QuizAttempt:
    result = await session.execute(
        select(QuizAttempt)
        .where(QuizAttempt.id == attempt_id)
        .options(
            selectinload(QuizAttempt.answers),
            selectinload(QuizAttempt.quiz),
        )
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.student_user_id != user_id and attempt.quiz.owner_user_id != user_id:
        raise HTTPException(status_code=403, detail="Attempt is not available")
    return attempt
