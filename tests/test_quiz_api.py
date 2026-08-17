import datetime
import uuid

from app.enums import QuizStatus
from app.routers import quiz_router


def quiz_payload(owner_user_id: uuid.UUID) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "owner_user_id": str(owner_user_id),
        "title": "Python basics",
        "description": "Intro quiz",
        "status": QuizStatus.DRAFT.value,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "questions": [],
    }


def attempt_payload(quiz_id: uuid.UUID, student_user_id: uuid.UUID) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "quiz_id": str(quiz_id),
        "student_user_id": str(student_user_id),
        "score": 1,
        "max_score": 1,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "answers": [],
    }


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_quiz_requires_user_header(client):
    response = client.post("/quizzes", json={"title": "Python basics"})

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "X-User-Id header is required"


def test_create_quiz_calls_service_with_current_user(client, monkeypatch):
    user_id = uuid.uuid4()
    captured = {}

    async def fake_create_quiz(data, current_user_id, session):
        captured["title"] = data.title
        captured["current_user_id"] = current_user_id
        captured["session"] = session
        return quiz_payload(current_user_id)

    monkeypatch.setattr(quiz_router, "create_quiz", fake_create_quiz)

    response = client.post(
        "/quizzes",
        headers={"X-User-Id": str(user_id)},
        json={"title": "Python basics", "questions": []},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Python basics"
    assert captured["title"] == "Python basics"
    assert captured["current_user_id"] == user_id
    assert captured["session"] is not None


def test_list_quizzes_returns_items(client, monkeypatch):
    user_id = uuid.uuid4()

    async def fake_list_my_quizzes(current_user_id, session):
        return [quiz_payload(current_user_id)]

    monkeypatch.setattr(quiz_router, "list_my_quizzes", fake_list_my_quizzes)

    response = client.get("/quizzes", headers={"X-User-Id": str(user_id)})

    assert response.status_code == 200
    assert response.json()[0]["owner_user_id"] == str(user_id)


def test_submit_attempt_returns_score(client, monkeypatch):
    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()

    async def fake_submit_attempt(quiz_id_arg, data, current_user_id, session):
        assert quiz_id_arg == quiz_id
        assert len(data.answers) == 1
        return attempt_payload(quiz_id_arg, current_user_id)

    monkeypatch.setattr(quiz_router, "submit_attempt", fake_submit_attempt)

    response = client.post(
        f"/quizzes/{quiz_id}/attempts",
        headers={"X-User-Id": str(user_id)},
        json={"answers": [{"question_id": str(uuid.uuid4()), "text_answer": "42"}]},
    )

    assert response.status_code == 200
    assert response.json()["score"] == 1
    assert response.json()["student_user_id"] == str(user_id)
