
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import SiteQuery, ReviewAction
from app.schemas import SiteQueryCreate, ReviewActionCreate

from app.ai_service import triage_query

app = FastAPI(
    title="Clinical Trial Assistant API",
    description="AI-powered study-site query triage",
    version="1.0.0"
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Clinical Triage Assistant API is running"
    }


@app.post("/api/queries", status_code=201)
def create_site_query(
    payload: SiteQueryCreate,
    db: Session = Depends(get_db)
):

    # 1. Classify the query and generate a draft
    triage_result = triage_query(payload.query_text)

    # 2. Prepare the database record

    query = SiteQuery(
        site_id=payload.site_id,
        query_text=payload.query_text,
        category=triage_result.category,
        requires_escalation=triage_result.requires_escalation,
        assigned_team=triage_result.assigned_team,
        ai_draft_response=triage_result.draft_response,
        status="pending_review"
    )

    # 3 Save the result to PostgreSQL

    try:
        db.add(query)
        db.commit()
        db.refresh(query)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save the site query"
        )

    # Step 4: Return the saved result
    return {
        "id": query.id,
        "site_id": query.site_id,
        "query_text": query.query_text,
        "category": query.category,
        "requires_escalation": query.requires_escalation,
        "assigned_team": query.assigned_team,
        "ai_draft_response": query.ai_draft_response,
        "status": query.status
    }


@app.post("/api/queries/{query_id}/review")
def review_site_query(
    query_id: str,
    payload: ReviewActionCreate,
    db: Session = Depends(get_db)
):
    # 1. Retrieve the original site query
    query = db.get(SiteQuery, query_id)

    if query is None:
        raise HTTPException(
            status_code=404,
            detail="Site query not found"
        )

    # 2. Prevent reviewing a completed query again
    if query.status != "pending_review":
        raise HTTPException(
            status_code=409,
            detail="This query has already been reviewed"
        )

    # 3. Validate the human review decision
    if payload.action == "edit":
        if not payload.edited_response or not payload.edited_response.strip():
            raise HTTPException(
                status_code=422,
                detail="An edited response is required for the edit action"
            )
    elif payload.edited_response is not None:
        raise HTTPException(
            status_code=422,
            detail="Edited response is only allowed for the edit action"
        )

    # 4. Determine the final status and response
    if payload.action == "approve":
        new_status = "approved"
        final_response = query.ai_draft_response

    elif payload.action == "edit":
        new_status = "approved"
        final_response = payload.edited_response.strip()

    else:
        new_status = "rejected"
        final_response = None

    # 5. Create a permanent audit record
    review = ReviewAction(
        query_id=query.id,
        reviewer_name=payload.reviewer_name,
        action=payload.action,
        edited_response=(
            final_response if payload.action == "edit" else None
        )
    )

    # 6. Save both changes in one database transaction
    try:
        query.status = new_status

        db.add(review)
        db.commit()
        db.refresh(query)
        db.refresh(review)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save the review decision"
        )

    # 7. Return the completed review
    return {
        "query_id": query.id,
        "review_id": review.id,
        "reviewer_name": review.reviewer_name,
        "action": review.action,
        "status": query.status,
        "final_response": final_response,
        "ai_draft_response": query.ai_draft_response
    }

@app.get("/api/queries")
def list_site_queries(db: Session = Depends(get_db)):
    queries = (
        db.query(SiteQuery)
        .order_by(SiteQuery.created_at.desc())
        .all()
    )

    results = []

    for query in queries:
        review = (
            db.query(ReviewAction)
            .filter(ReviewAction.query_id == query.id)
            .order_by(ReviewAction.created_at.desc())
            .first()
        )

        final_response = None

        if query.status == "approved" and review:
            if review.action == "edit":
                final_response = review.edited_response
            elif review.action == "approve":
                final_response = query.ai_draft_response

        results.append({
            "id": query.id,
            "site_id": query.site_id,
            "query_text": query.query_text,
            "category": query.category,
            "requires_escalation": query.requires_escalation,
            "assigned_team": query.assigned_team,
            "ai_draft_response": query.ai_draft_response,
            "final_response": final_response,
            "status": query.status,
            "created_at": query.created_at,
        })

    return results

@app.get("/api/queries/{query_id}")
def get_site_query(
    query_id: str,
    db: Session = Depends(get_db)
):
    query = db.get(SiteQuery, query_id)

    if query is None:
        raise HTTPException(
            status_code=404,
            detail="Site query not found"
        )

    reviews = (
        db.query(ReviewAction)
        .filter(ReviewAction.query_id == query_id)
        .order_by(ReviewAction.created_at.desc())
        .all()
    )

    return {
        "id": query.id,
        "site_id": query.site_id,
        "query_text": query.query_text,
        "category": query.category,
        "requires_escalation": query.requires_escalation,
        "assigned_team": query.assigned_team,
        "ai_draft_response": query.ai_draft_response,
        "status": query.status,
        "created_at": query.created_at,
        "review_history": [
            {
                "id": review.id,
                "reviewer_name": review.reviewer_name,
                "action": review.action,
                "edited_response": review.edited_response,
                "created_at": review.created_at
            }
            for review in reviews
        ]
    }
