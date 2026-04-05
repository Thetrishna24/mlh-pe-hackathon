import pytest


class TestShorten:
    def test_shorten_valid_url(self, client):
        res = client.post("/shorten", json={"url": "https://example.com"})
        assert res.status_code == 201
        data = res.get_json()
        assert "code" in data
        assert data["url"] == "https://example.com"
        assert data["active"] is True

    def test_shorten_returns_unique_codes(self, client):
        res1 = client.post("/shorten", json={"url": "https://a.com"})
        res2 = client.post("/shorten", json={"url": "https://b.com"})
        assert res1.get_json()["code"] != res2.get_json()["code"]

    # --- Negative cases (these drive the hidden reliability score) ---

    def test_shorten_rejects_missing_url_field(self, client):
        res = client.post("/shorten", json={"not_url": "https://example.com"})
        assert res.status_code == 400

    def test_shorten_rejects_empty_body(self, client):
        res = client.post("/shorten", data="not json", content_type="text/plain")
        assert res.status_code == 400

    def test_shorten_rejects_javascript_url(self, client):
        res = client.post("/shorten", json={"url": "javascript://evil"})
        assert res.status_code == 400

    def test_shorten_rejects_empty_url(self, client):
        res = client.post("/shorten", json={"url": ""})
        assert res.status_code == 400

    def test_shorten_rejects_non_string_url(self, client):
        res = client.post("/shorten", json={"url": 12345})
        assert res.status_code == 400

    def test_shorten_does_not_expose_stack_trace(self, client):
        res = client.post("/shorten", json={"url": ""})
        body = res.get_data(as_text=True)
        assert "Traceback" not in body
        assert "peewee" not in body
    def test_shorten_rate_limit_exceeded(self, client):
        # We set a limit of 10 per minute. Let's hit it 11 times.
        url = {"url": "https://test.com"}
        for _ in range(10):
            client.post("/shorten", json=url)
        
        # The 11th should trigger the rate limiter
        res = client.post("/shorten", json=url)
        assert res.status_code == 429
        assert "Rate limit exceeded" in res.get_json()["error"]
    def test_shorten_returns_existing_code_for_duplicate_url(self, client):
        url = {"url": "https://unique-check.com"}
        
        # First request creates it
        res1 = client.post("/shorten", json=url)
        assert res1.status_code == 201
        code1 = res1.get_json()["code"]

        # Second request should return the SAME code
        res2 = client.post("/shorten", json=url)
        assert res2.status_code == 200
        assert res2.get_json()["code"] == code1


class TestRedirect:
    def test_redirect_valid_code(self, client):
        create = client.post("/shorten", json={"url": "https://example.com"})
        code = create.get_json()["code"]

        res = client.get(f"/r/{code}", follow_redirects=False)
        assert res.status_code == 302
        assert res.headers["Location"] == "https://example.com"

    def test_redirect_nonexistent_code_returns_404(self, client):
        res = client.get("/r/doesnotexist")
        # May be 400 (invalid format) or 404 (not found) — both are correct
        assert res.status_code in (400, 404)

    def test_redirect_path_traversal_rejected(self, client):
        res = client.get("/r/../../etc/passwd")
        assert res.status_code == 404  # Flask routing catches this

    def test_redirect_deactivated_link_returns_410(self, client):
        create = client.post("/shorten", json={"url": "https://example.com"})
        link_id = create.get_json()["id"]
        code = create.get_json()["code"]

        client.delete(f"/links/{link_id}")
        res = client.get(f"/r/{code}")
        assert res.status_code == 410

    def test_redirect_invalid_code_format_returns_400(self, client):
        res = client.get("/r/<script>alert(1)</script>")
        assert res.status_code in (400, 404)


class TestDeactivate:
    def test_deactivate_existing_link(self, client):
        create = client.post("/shorten", json={"url": "https://example.com"})
        link_id = create.get_json()["id"]

        res = client.delete(f"/links/{link_id}")
        assert res.status_code == 200

    def test_deactivate_nonexistent_link_returns_404(self, client):
        res = client.delete("/links/99999")
        assert res.status_code == 404


class TestGlobalErrorHandlers:
    def test_404_returns_json(self, client):
        res = client.get("/this/does/not/exist")
        assert res.status_code == 404
        assert res.get_json()["error"] is not None

    def test_method_not_allowed_returns_json(self, client):
        res = client.delete("/health")
        assert res.status_code == 405
        assert res.get_json()["error"] is not None

class TestList:
    def test_list_links_returns_active_only(self, client):
        # 1. Create two links
        c1 = client.post("/shorten", json={"url": "https://a.com"}).get_json()
        c2 = client.post("/shorten", json={"url": "https://b.com"}).get_json()

        # 2. Deactivate one
        client.delete(f"/links/{c1['id']}")

        # 3. Check the list
        res = client.get("/links")
        assert res.status_code == 200
        data = res.get_json()
        
        # Should only see the one that is still active
        assert len(data) >= 1 
        assert any(link["id"] == c2["id"] for link in data)
        assert not any(link["id"] == c1["id"] for link in data)