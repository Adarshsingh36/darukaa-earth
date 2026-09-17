from tests.conftest import SAMPLE_POLYGON


def _create_site(client, auth_headers):
    project_resp = client.post("/api/projects", headers=auth_headers, json={"name": "Metrics Project"})
    project_id = project_resp.json()["id"]
    site_resp = client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Metrics Site", "geometry": SAMPLE_POLYGON},
    )
    return site_resp.json()["id"]


def test_create_and_list_metrics(client, auth_headers):
    site_id = _create_site(client, auth_headers)

    create_resp = client.post(
        f"/api/sites/{site_id}/metrics",
        headers=auth_headers,
        json={
            "recorded_at": "2025-01-01",
            "carbon_tonnes": 1200,
            "biodiversity_index": 48,
            "tree_cover_percentage": 54,
            "species_count": 32,
        },
    )
    assert create_resp.status_code == 201

    list_resp = client.get(f"/api/sites/{site_id}/metrics", headers=auth_headers)
    assert list_resp.status_code == 200
    metrics = list_resp.json()
    assert len(metrics) == 1
    assert metrics[0]["carbon_tonnes"] == 1200


def test_metrics_for_nonexistent_site_returns_404(client, auth_headers):
    resp = client.get("/api/sites/00000000-0000-0000-0000-000000000000/metrics", headers=auth_headers)
    assert resp.status_code == 404


def test_dashboard_summary_reflects_created_data(client, auth_headers):
    site_id = _create_site(client, auth_headers)
    client.post(
        f"/api/sites/{site_id}/metrics",
        headers=auth_headers,
        json={
            "recorded_at": "2025-01-01",
            "carbon_tonnes": 1000,
            "biodiversity_index": 50,
            "tree_cover_percentage": 55,
            "species_count": 20,
        },
    )

    resp = client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_projects"] == 1
    assert summary["total_sites"] == 1
    assert summary["total_carbon_tonnes"] == 1000
    assert summary["average_biodiversity_index"] == 50


def test_dashboard_summary_only_includes_current_users_data(client):
    first_user = client.post(
        "/api/auth/register",
        json={
            "name": "First User",
            "email": "first@example.com",
            "password": "supersecret123",
        },
    )
    assert first_user.status_code == 201
    first_headers = {
        "Authorization": f"Bearer {first_user.json()['access_token']}"
    }

    first_project = client.post(
        "/api/projects",
        headers=first_headers,
        json={"name": "First User Project"},
    )
    assert first_project.status_code == 201

    first_site = client.post(
        f"/api/projects/{first_project.json()['id']}/sites",
        headers=first_headers,
        json={"name": "First User Site", "geometry": SAMPLE_POLYGON},
    )
    assert first_site.status_code == 201

    first_site_id = first_site.json()["id"]

    metric = client.post(
        f"/api/sites/{first_site_id}/metrics",
        headers=first_headers,
        json={
            "recorded_at": "2025-01-01",
            "carbon_tonnes": 500,
            "biodiversity_index": 40,
            "tree_cover_percentage": 50,
            "species_count": 15,
        },
    )
    assert metric.status_code == 201

    second_user = client.post(
        "/api/auth/register",
        json={
            "name": "Second User",
            "email": "second@example.com",
            "password": "supersecret123",
        },
    )
    assert second_user.status_code == 201
    second_headers = {
        "Authorization": f"Bearer {second_user.json()['access_token']}"
    }

    second_project = client.post(
        "/api/projects",
        headers=second_headers,
        json={"name": "Second User Project"},
    )
    assert second_project.status_code == 201

    second_site = client.post(
        f"/api/projects/{second_project.json()['id']}/sites",
        headers=second_headers,
        json={"name": "Second User Site", "geometry": SAMPLE_POLYGON},
    )
    assert second_site.status_code == 201

    second_site_id = second_site.json()["id"]

    metric = client.post(
        f"/api/sites/{second_site_id}/metrics",
        headers=second_headers,
        json={
            "recorded_at": "2025-01-01",
            "carbon_tonnes": 1000,
            "biodiversity_index": 80,
            "tree_cover_percentage": 70,
            "species_count": 30,
        },
    )
    assert metric.status_code == 201

    first_dashboard = client.get(
        "/api/dashboard/summary",
        headers=first_headers,
    )
    assert first_dashboard.status_code == 200

    first_summary = first_dashboard.json()
    assert first_summary["total_projects"] == 1
    assert first_summary["total_sites"] == 1
    assert first_summary["total_carbon_tonnes"] == 500
    assert first_summary["average_biodiversity_index"] == 40

    second_dashboard = client.get(
        "/api/dashboard/summary",
        headers=second_headers,
    )
    assert second_dashboard.status_code == 200

    second_summary = second_dashboard.json()
    assert second_summary["total_projects"] == 1
    assert second_summary["total_sites"] == 1
    assert second_summary["total_carbon_tonnes"] == 1000
    assert second_summary["average_biodiversity_index"] == 80