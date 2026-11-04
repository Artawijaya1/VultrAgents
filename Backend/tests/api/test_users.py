def test_user_crud(client):
    created = client.post(
        "/api/v1/users/",
        json={"email": "person@example.com", "full_name": "Test Person"},
    )
    assert created.status_code == 201
    user = created.json()
    assert user["email"] == "person@example.com"

    listed = client.get("/api/v1/users/")
    assert listed.status_code == 200
    assert [entry["id"] for entry in listed.json()] == [user["id"]]

    updated = client.patch(
        f"/api/v1/users/{user['id']}",
        json={"full_name": "Updated Person"},
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Person"

    deleted = client.delete(f"/api/v1/users/{user['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/users/{user['id']}").status_code == 404


def test_duplicate_user_email_returns_conflict(client):
    payload = {"email": "duplicate@example.com"}
    assert client.post("/api/v1/users/", json=payload).status_code == 201

    response = client.post("/api/v1/users/", json=payload)

    assert response.status_code == 409
    assert response.json() == {"detail": "A user with this email already exists."}

