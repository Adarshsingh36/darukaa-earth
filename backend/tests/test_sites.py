from tests.conftest import SAMPLE_POLYGON


def _create_project(client, auth_headers, name="Test Project"):
    resp = client.post("/api/projects", headers=auth_headers, json={"name": name})
    return resp.json()["id"]


def test_create_site_with_valid_polygon_calculates_area(client, auth_headers):
    project_id = _create_project(client, auth_headers)

    resp = client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Ridge Plot", "description": "Test plot", "geometry": SAMPLE_POLYGON},
    )
    assert resp.status_code == 201
    site = resp.json()
    assert site["name"] == "Ridge Plot"
    # A ~1.1km x 1km box near the equator should be roughly 100-120 hectares.
    assert 90 < site["area_hectares"] < 130
    assert site["geometry"]["type"] == "Polygon"


def test_site_geometry_round_trips_correctly(client, auth_headers):
    project_id = _create_project(client, auth_headers)
    create_resp = client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Ridge Plot", "geometry": SAMPLE_POLYGON},
    )
    site_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/sites/{site_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    returned_coords = get_resp.json()["geometry"]["coordinates"][0]
    original_coords = SAMPLE_POLYGON["coordinates"][0]
    for (rlng, rlat), (olng, olat) in zip(returned_coords, original_coords, strict=False):
        assert abs(rlng - olng) < 1e-6
        assert abs(rlat - olat) < 1e-6


def test_create_site_rejects_unclosed_ring(client, auth_headers):
    project_id = _create_project(client, auth_headers)
    bad_geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1]]]}

    resp = client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Bad Polygon", "geometry": bad_geometry},
    )
    assert resp.status_code == 422


def test_create_site_rejects_out_of_range_coordinates(client, auth_headers):
    project_id = _create_project(client, auth_headers)
    bad_geometry = {
        "type": "Polygon",
        "coordinates": [[[200, 12], [201, 12], [201, 13], [200, 13], [200, 12]]],
    }

    resp = client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Out of Range", "geometry": bad_geometry},
    )
    assert resp.status_code == 422


def test_create_site_for_nonexistent_project_returns_404(client, auth_headers):
    resp = client.post(
        "/api/projects/00000000-0000-0000-0000-000000000000/sites",
        headers=auth_headers,
        json={"name": "Orphan Site", "geometry": SAMPLE_POLYGON},
    )
    assert resp.status_code == 404


def test_list_sites_for_project(client, auth_headers):
    project_id = _create_project(client, auth_headers)
    client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Site A", "geometry": SAMPLE_POLYGON},
    )
    client.post(
        f"/api/projects/{project_id}/sites",
        headers=auth_headers,
        json={"name": "Site B", "geometry": SAMPLE_POLYGON},
    )

    resp = client.get(f"/api/projects/{project_id}/sites", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_sites_require_auth(client):
    resp = client.get("/api/projects/00000000-0000-0000-0000-000000000000/sites")
    assert resp.status_code == 401
