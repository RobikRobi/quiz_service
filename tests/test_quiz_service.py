import uuid
from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from app.enums import QuestionType
from app.services.quiz_service import _ensure_owner, _grade_question


def test_ensure_owner_allows_owner():
    user_id = uuid.uuid4()
    quiz = SimpleNamespace(owner_user_id=user_id)

    _ensure_owner(quiz, user_id)


def test_ensure_owner_rejects_another_user():
    quiz = SimpleNamespace(owner_user_id=uuid.uuid4())

    with pytest.raises(HTTPException) as exc_info:
        _ensure_owner(quiz, uuid.uuid4())

    assert exc_info.value.status_code == 403


def test_grade_text_question_is_case_insensitive():
    question = SimpleNamespace(
        question_type=QuestionType.TEXT,
        accepted_answers=["FastAPI"],
        points=2,
    )
    answer = SimpleNamespace(text_answer=" fastapi ")

    is_correct, points = _grade_question(question, answer)

    assert is_correct is True
    assert points == 2


def test_grade_single_choice_requires_exact_correct_option():
    correct_option_id = uuid.uuid4()
    wrong_option_id = uuid.uuid4()
    question = SimpleNamespace(
        question_type=QuestionType.SINGLE_CHOICE,
        options=[
            SimpleNamespace(id=correct_option_id, is_correct=True),
            SimpleNamespace(id=wrong_option_id, is_correct=False),
        ],
        points=1,
    )
    answer = SimpleNamespace(selected_option_ids=[correct_option_id])

    is_correct, points = _grade_question(question, answer)

    assert is_correct is True
    assert points == 1


def test_grade_multiple_choice_rejects_partial_answer():
    first_option_id = uuid.uuid4()
    second_option_id = uuid.uuid4()
    question = SimpleNamespace(
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=[
            SimpleNamespace(id=first_option_id, is_correct=True),
            SimpleNamespace(id=second_option_id, is_correct=True),
        ],
        points=3,
    )
    answer = SimpleNamespace(selected_option_ids=[first_option_id])

    is_correct, points = _grade_question(question, answer)

    assert is_correct is False
    assert points == 0
