"""
Integration tests for the RAG Pipeline API.

These tests require a running PostgreSQL/Supabase instance with the schema applied.
Set DATABASE_URL, OPENROUTER_API_KEY in your environment before running.

Run with:
    pytest tests/ -v
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "embedding_model" in body
    assert "openrouter_model" in body


def test_root_redirect() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "docs" in response.json().get("message", "").lower()


# ── Documents ─────────────────────────────────────────────────────────────────

SAMPLE_DOC = {
    "title": "Test Document – Introduction",
    "content": "This is a test document about workplace safety procedures at Acme Corp.",
    "source": "test_document.md",
    "metadata": {"category": "test"},
}


def test_ingest_single_document() -> None:
    response = client.post("/api/documents", json=SAMPLE_DOC)
    assert response.status_code == 201
    body = response.json()
    assert body["inserted"] == 1
    assert len(body["ids"]) == 1


def test_ingest_batch() -> None:
    docs = {
        "documents": [
            {
                "title": f"Batch Test Doc {i}",
                "content": f"Content for batch document number {i}. This is test content.",
                "source": "batch_test.md",
                "metadata": {"index": i},
            }
            for i in range(5)
        ]
    }
    response = client.post("/api/documents/batch", json=docs)
    assert response.status_code == 201
    body = response.json()
    assert body["inserted"] == 5


def test_list_documents() -> None:
    response = client.get("/api/documents")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "items" in body
    assert isinstance(body["items"], list)


def test_delete_document() -> None:
    # First, insert a document to delete
    insert_response = client.post(
        "/api/documents",
        json={
            "title": "Document to Delete",
            "content": "This document will be deleted as part of the test suite.",
            "source": "deletable.md",
            "metadata": {},
        },
    )
    assert insert_response.status_code == 201
    doc_id = insert_response.json()["ids"][0]

    # Delete it
    delete_response = client.delete(f"/api/documents/{doc_id}")
    assert delete_response.status_code == 204

    # Confirm 404 on second delete
    second_delete = client.delete(f"/api/documents/{doc_id}")
    assert second_delete.status_code == 404


# ── Query ─────────────────────────────────────────────────────────────────────


def test_query_returns_answer() -> None:
    # Ensure at least one document is present
    client.post("/api/documents", json=SAMPLE_DOC)

    response = client.post(
        "/api/query",
        json={
            "query": "What are the workplace safety procedures?",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert isinstance(body["answer"], str)
    assert len(body["answer"]) > 0
    assert "sources" in body
    assert isinstance(body["sources"], list)


def test_query_validation() -> None:
    # Empty query should fail validation
    response = client.post("/api/query", json={"query": "", "top_k": 3})
    assert response.status_code == 422

    # top_k out of range
    response = client.post("/api/query", json={"query": "test", "top_k": 100})
    assert response.status_code == 422
