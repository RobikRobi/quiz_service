import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.enums import QuestionType, QuizStatus


class AnswerOptionCreate(BaseModel):
    text: str
    is_correct: bool = False
    position: int = 0


class QuestionCreate(BaseModel):
    text: str
    question_type: QuestionType
    position: int = 0
    points: int = Field(default=1, ge=1)
    accepted_answers: list[str] | None = None
    options: list[AnswerOptionCreate] = Field(default_factory=list)


class QuizCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    questions: list[QuestionCreate] = Field(default_factory=list)


class QuizUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: QuizStatus | None = None
    questions: list[QuestionCreate] | None = None


class AnswerOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    is_correct: bool
    position: int


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    text: str
    question_type: QuestionType
    position: int
    points: int
    accepted_answers: list[str] | None
    options: list[AnswerOptionRead]


class QuizRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    title: str
    description: str | None
    status: QuizStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    questions: list[QuestionRead]


class QuestionAnswerCreate(BaseModel):
    question_id: uuid.UUID
    selected_option_ids: list[uuid.UUID] | None = None
    text_answer: str | None = None


class AttemptCreate(BaseModel):
    answers: list[QuestionAnswerCreate]


class AttemptAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    selected_option_ids: list[str] | None
    text_answer: str | None
    is_correct: bool
    points_awarded: int


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quiz_id: uuid.UUID
    student_user_id: uuid.UUID
    score: int
    max_score: int
    created_at: datetime.datetime
    answers: list[AttemptAnswerRead]
