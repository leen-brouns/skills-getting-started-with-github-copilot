from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_index_is_available():
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "Mergington High School" in response.text


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert {"description", "schedule", "max_participants", "participants"} <= set(
        activities["Chess Club"]
    )


def test_signup_adds_participant():
    email = "new.student@mergington.edu"

    response = client.post("/activities/Art Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art Club"}
    assert email in client.get("/activities").json()["Art Club"]["participants"]


def test_duplicate_signup_is_rejected():
    email = "duplicate.student@mergington.edu"
    client.post("/activities/Art Club/signup", params={"email": email})

    response = client.post("/activities/Art Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    participants = client.get("/activities").json()["Art Club"]["participants"]
    assert participants.count(email) == 1


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email():
    response = client.post("/activities/Art Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant():
    email = "leaving.student@mergington.edu"
    client.post("/activities/Art Club/signup", params={"email": email})

    response = client.delete(f"/activities/Art Club/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Art Club"}
    assert email not in client.get("/activities").json()["Art Club"]["participants"]


def test_unregister_rejects_missing_participant():
    response = client.delete(
        "/activities/Art Club/participants/not.registered@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/participants/student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_and_unregister_round_trip():
    email = "round.trip@mergington.edu"

    signup_response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    unregister_response = client.delete(
        f"/activities/Chess Club/participants/{email}"
    )

    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]