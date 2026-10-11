import { useState, useEffect } from "react";
import "./App.css";

type SiteQuery = {
   id: string;
   site_id: string;
   query_text: string;
   category: string | null;
   requires_escalation: boolean | null;
   assigned_team: string | null;
   ai_draft_response: string | null;
   status: string;
   created_at: string;
   final_response?: string | null;
}


function App() {
  const [queries, setQueries] = useState<SiteQuery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const totalQueries = queries.length;

  const pendingReviewCount = queries.filter((query) => query.status === "pending_review").length;

  const escalationCount = queries.filter((query) => query.requires_escalation === true).length;

  const reviewedCount = queries.filter((query) => query.status === "approved" || query.status === "rejected").length;

  const [siteId, setSiteId] = useState("");
  const [queryText, setQueryText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [reviewingQueryId, setReviewingQueryId] = useState<string | null>(null);
  const [reviewerName, setReviewerName] = useState("Clinical Reviewer");
  const [editedResponse, setEditedResponse] = useState("");
  const [isReviewing, setIsReviewing] = useState(false);


  useEffect(() => {

    async function fetchQueries() {

      try {
        const response = await fetch("/api/queries");

        if(!response.ok) {
          throw new Error("Failed to retrieve site queries");
        }

        const data: SiteQuery[] = await response.json();

        setQueries(data);
      } catch (error) {
        console.error("Error fetching queries: ", error);
        setError(
          error instanceof Error ? error.message : "Unexpected error"
        );

      } finally {
        setIsLoading(false);
      }


    }

    fetchQueries();
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {

    event.preventDefault();

    const trimmedSiteId = siteId.trim();
    const trimmedQueryText = queryText.trim();

    if(!trimmedSiteId || !trimmedQueryText) {
       setError("Site ID and a query are required.");
       return;
    }



    setIsSubmitting(true);
    setError("");

    try {

      const response = await fetch("/api/queries", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          site_id: trimmedSiteId,
          query_text: trimmedQueryText,
        }),
      });


      if(!response.ok) {
        throw new Error(`Failed to submit study-site query (HTTP ${response.status})`);
      }

      const newQuery: SiteQuery = await response.json();

      setQueries((previousQueries) => [
        newQuery,
        ...previousQueries
      ]);

      setSiteId("");
      setQueryText("");



    } catch (error) {

      setError(error instanceof Error ? error.message : "An error occurred");

    } finally {
      setIsSubmitting(false);

    }

  }

  function startReview(query: SiteQuery) {
    setReviewingQueryId(query.id);
    setEditedResponse(query.ai_draft_response ?? "");
    setError("");
  }

  async function handleReview(
    queryId: string,
    action: "approve" | "edit" | "reject"
  ) {
    const trimmedReviewerName = reviewerName.trim();

    if(!trimmedReviewerName) {
      setError("Reviewer name is required.");
      return;
    }

    if(action === "edit" && !editedResponse.trim()) {
      setError("An edited response is required.");
      return;
    }

    setIsReviewing(true);
    setError("");

    try {

        const response = await fetch(`/api/queries/${queryId}/review`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              reviewer_name: trimmedReviewerName,
              action,
              edited_response: action === "edit" ? editedResponse : null,
            })
        });

        const data = await response.json();

        if(!response.ok) {
          throw new Error("Error in submitting review: ", data.error);
        }

        setQueries((previousQueries) =>
          previousQueries.map((previousQuery) => previousQuery.id === queryId ? {
          ...previousQuery,
          status: data.status,
          final_response: data.final_response,
        } : previousQuery));

        setReviewingQueryId(null);
        setEditedResponse("");




    } catch (error) {

      setError(error instanceof Error ? error.message : "Unexpected error occurred.");

    } finally {
      setIsReviewing(false);

    }

  }


  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <p className="eyebrow">CLINICAL OPERATIONS</p>
        <h1>Study-Site Dashboard</h1>
        <p>Review and manage AI-triaged study-site requests.</p>
      </header>

      <section className="stats-section" aria-label="Query-statistics">
        <div className="stats-grid-section">
          <div className="stat-card">
            <p className="stat-label">
              Total Queries
            </p>
            <h3 className="stat-count">{totalQueries}</h3>
            <p className="stat-description">All submitted queries</p>
          </div>

          <div className="stat-card">
            <p className="stat-label">
              Pending Review
            </p>
            <h3>{pendingReviewCount}</h3>
            <p className="stat-description">Awaiting human review</p>

          </div>

          <div className="stat-card">
            <p className="stat-label">
              Escalations
            </p>
            <h3>{escalationCount}</h3>
            <p className="stat-description">Flagged for escalation</p>

          </div>

          <div className="stat-card">
            <p className="stat-label">
              Reviewed
            </p>
            <h3>{reviewedCount}</h3>
            <p className="stat-description">Approved or rejected</p>

          </div>
        </div>




      </section>

      <section className="form-section">
        <h2>Submit Study-Site Query</h2>

        <form onSubmit={handleSubmit} className="query-form">
          <div className="form-group">
              <label htmlFor="site-id">Site ID</label>
              <input
                    id="site-id"
                    type="text"
                    placeholder="e.g. 042"
                    value={siteId}
                    onChange={(e) => setSiteId(e.target.value)}
                    className="form-field"
                    maxLength={50}
                    required
              />

          </div>

          <div className="form-group">
              <label htmlFor="query-text">Query Description</label>
              <textarea
                     id="query-text"
                     placeholder="Describe the study-site request..."
                     value={queryText}
                     onChange={(event) => setQueryText(event.target.value)}
                     maxLength={4000}
                     required
                     className="query-field"
              />

              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Submitting..." : "Submit for Triage"}
              </button>

          </div>



        </form>

      </section>

      <section className="query-section">
        <h2>Submitted Queries</h2>

        {isLoading && (
          <p>Loading queries...</p>
        )}

        {error && (
          <p className="error">{error}</p>
        )}

        {!isLoading && !error && queries.length === 0 && (
          <p>No queries have been submitted yet.</p>
        )}

        {!isLoading && !error && queries.map((query) => (
          <article key={query.id} className="query-card">
            <div className="query-card-header">
              <h3>Site {query.site_id}</h3>
              <span className="status-badge">{query.status.replaceAll("_", " ").replace(/^\b\w/g, (char) => char.toUpperCase())}</span>
            </div>

            <p>{query.query_text}</p>

            <div className="query-details">
              <p><strong>Category:</strong> {query.category ?? "Unclassified"}</p>
              <p><strong>Assigned Team:</strong> {query.assigned_team ?? "Not assigned"}</p>
              <p>
                <strong>Escalation:</strong>{" "}
                {query.requires_escalation ? "Required" : "Not required"}
              </p>

            </div>

            <div className="draft-response">
              <strong>AI Draft Response</strong>
              <p>{query.ai_draft_response ?? "Not available"}</p>
            </div>

            {query.status === "approved" && query.final_response && (
              <div className="draft-response">
                <strong>Final Human-Approved Response</strong>
                <p>{query.final_response}</p>
              </div>
            )}

            {query.status === "pending_review" && (
              <div className="review-section">
                {reviewingQueryId !== query.id ? (
                  <button
                         type="button"
                         className="review-button"
                         onClick={() => startReview(query)}
                  >
                    Review Query
                  </button>
                ) : (
                  <div className="review-panel">
                    <h4>Human Review</h4>

                    <div className="review-form-group">
                        <label
                            htmlFor={`reviewer-${query.id}`}
                        >
                            Reviewer Name
                        </label>

                        <input
                            id={`reviewer-${query.id}`}
                            type="text"
                            value={reviewerName}
                            onChange={(event) => setReviewerName(event.target.value)}
                            maxLength={50}
                        />
                    </div>

                    <div className="review-form-group">
                        <label
                            htmlFor={`response-${query.id}`}
                        >
                          Response for Review

                        </label>

                        <textarea
                            id={`response-${query.id}`}
                            value={editedResponse}
                            onChange={(event) => setEditedResponse(event.target.value)}
                            rows={5}

                        />

                    </div>


                    <div className="review-actions">
                      <button type="button" disabled={isReviewing} onClick={() => handleReview(query.id, "approve")}>
                        Approve Original
                      </button>

                      <button type="button" disabled={isReviewing} onClick={() => handleReview(query.id, "edit")}>
                        Save Edited Response
                      </button>

                      <button type="button" disabled={isReviewing} onClick={() => handleReview(query.id, "reject")}>
                        Reject
                      </button>

                      <button type="button" disabled={isReviewing} onClick={() => setReviewingQueryId(null)}>
                        Cancel
                      </button>
                    </div>

                  </div>
                )}

              </div>
            )}

          </article>
        ))}

      </section>
    </main>
  );

}

export default App
