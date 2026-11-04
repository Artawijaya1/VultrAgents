def test_admin_can_list_and_update_user_profiles(client):
    profile = client.get("/api/v1/auth/me").json()

    listed = client.get("/api/v1/users/")
    assert listed.status_code == 200
    assert [entry["id"] for entry in listed.json()] == [profile["id"]]

    updated = client.patch(
        f"/api/v1/users/{profile['id']}",
        json={"full_name": "Updated Admin", "is_active": False},
    )

    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Admin"
    assert updated.json()["is_active"] is False
