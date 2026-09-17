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
