def test_item_crud(client):
    created = client.post(
        "/api/v1/items/",
        json={"title": "First item", "description": "Details"},
    )
    assert created.status_code == 201
    item = created.json()

    listed = client.get("/api/v1/items/")
    assert listed.status_code == 200
    assert listed.json()[0]["title"] == "First item"

    updated = client.patch(
        f"/api/v1/items/{item['id']}",
        json={"title": "Updated item"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated item"

    deleted = client.delete(f"/api/v1/items/{item['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/items/{item['id']}").status_code == 404


def test_item_requires_existing_owner(client):
    response = client.post(
        "/api/v1/items/",
        json={"title": "Owned item", "owner_id": 999},
    )

    assert response.status_code == 404


def test_item_title_cannot_be_cleared(client):
    item = client.post("/api/v1/items/", json={"title": "Keep title"}).json()

    response = client.patch(f"/api/v1/items/{item['id']}", json={"title": None})

    assert response.status_code == 422

