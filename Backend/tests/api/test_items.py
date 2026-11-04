from app.api.deps import get_current_identity
from app.main import app
from app.schemas.token import SupabaseIdentity


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


def test_item_cannot_be_created_for_another_user(client):
    response = client.post(
        "/api/v1/items/",
        json={"title": "Owned item", "owner_id": 999},
    )

    assert response.status_code == 403


def test_item_is_not_visible_to_another_user(client):
    item = client.post("/api/v1/items/", json={"title": "Private item"}).json()
    app.dependency_overrides[get_current_identity] = lambda: SupabaseIdentity(
        id="908606b9-7da1-4e8d-a5a2-f2af3423c437",
        email="other@example.com",
        app_metadata={},
    )

    response = client.get(f"/api/v1/items/{item['id']}")

    assert response.status_code == 404


def test_item_title_cannot_be_cleared(client):
    item = client.post("/api/v1/items/", json={"title": "Keep title"}).json()

    response = client.patch(f"/api/v1/items/{item['id']}", json={"title": None})

    assert response.status_code == 422
