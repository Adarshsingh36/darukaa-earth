def test_create_project_requires_auth(client):
    resp = client.post("/api/projects", json={"name": "No Auth Project"})
    assert resp.status_code == 401


def test_create_and_retrieve_project(client, auth_headers):
    create_resp = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "name": "Mangrove Restoration",
            "description": "Coastal mangrove replanting",
            "location": "Sundarbans",
            "start_date": "2024-03-01",
        },
    )
    assert create_resp.status_code == 201
    project = create_resp.json()
    assert project["name"] == "Mangrove Restoration"
    assert project["site_count"] == 0

    get_resp = client.get(f"/api/projects/{project['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == project["id"]


def test_list_projects_returns_created_projects(client, auth_headers):
    client.post("/api/projects", headers=auth_headers, json={"name": "Project One"})
    client.post("/api/projects", headers=auth_headers, json={"name": "Project Two"})

    resp = client.get("/api/projects", headers=auth_headers)
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert names == {"Project One", "Project Two"}


def test_get_nonexistent_project_returns_404(client, auth_headers):
    resp = client.get("/api/projects/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_project_removes_it(client, auth_headers):
    create_resp = client.post("/api/projects", headers=auth_headers, json={"name": "Temp Project"})
    project_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/api/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 404
