
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_db
from app.models import SiteQuery, ReviewAction


def test_query_cannot_be_reviewed_twice():
    # 1. Create a temporary SQLite database.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
    )

    # 2. Replace the application's database dependency.
    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        # 3. Insert a fictional site query.
        with TestingSessionLocal() as db:
            query = SiteQuery(
                site_id="SITE-110",
                query_text="Site 110 needs an IRB amendment reviewed.",
                category="regulatory",
                requires_escalation=True,
                assigned_team="Regulatory Affairs",
                ai_draft_response="Thank you for your inquiry.",
                status="pending_review",
            )

            db.add(query)
            db.commit()
            query_id = query.id

        # 4. Approve the query.
        with TestClient(app) as client:
            first_response = client.post(
                f"/api/queries/{query_id}/review",
                json={
                    "reviewer_name": "Test Reviewer",
                    "action": "approve",
                },
            )

            assert first_response.status_code == 200
            assert first_response.json()["status"] == "approved"

            # 5. Attempt to reject the same query.
            second_response = client.post(
                f"/api/queries/{query_id}/review",
                json={
                    "reviewer_name": "Second Reviewer",
                    "action": "reject",
                },
            )

            assert second_response.status_code == 409

        # 6. Verify the original decision was preserved.
        with TestingSessionLocal() as db:
            saved_query = db.get(SiteQuery, query_id)

            assert saved_query.status == "approved"

            reviews = (
                db.query(ReviewAction)
                .filter(ReviewAction.query_id == query_id)
                .all()
            )

            assert len(reviews) == 1
            assert reviews[0].action == "approve"

    finally:
        # 7. Restore the normal application dependency.
        app.dependency_overrides.clear()
        test_engine.dispose()
