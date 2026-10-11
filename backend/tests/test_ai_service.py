
from app.ai_service import (
    TriageResult,
    enforce_safety_escalation,
    triage_query,
)


def test_serious_adverse_event_requires_escalation():
    result = TriageResult(
        category="logistics",
        requires_escalation=False,
        assigned_team="Site Logistics",
        draft_response="Thank you for your inquiry.",
    )

    updated_result = enforce_safety_escalation(
        "Site 109 reported a serious adverse event.",
        result,
    )

    assert updated_result.category == "safety"
    assert updated_result.requires_escalation is True
    assert updated_result.assigned_team == "Drug Safety"


def test_regulatory_query_does_not_trigger_safety_override():
    result = TriageResult(
        category="regulatory",
        requires_escalation=True,
        assigned_team="Regulatory Affairs",
        draft_response="We will review the amendment.",
    )

    updated_result = enforce_safety_escalation(
        "Site 110 needs an IRB amendment reviewed.",
        result,
    )

    assert updated_result.category == "regulatory"
    assert updated_result.requires_escalation is True
    assert updated_result.assigned_team == "Regulatory Affairs"


def test_safety_override_is_case_insensitive():
    result = TriageResult(
        category="other",
        requires_escalation=False,
        assigned_team="Clinical Operations",
        draft_response="Thank you for your inquiry.",
    )

    updated_result = enforce_safety_escalation(
        "SITE 109 REPORTED AN SAE.",
        result,
    )

    assert updated_result.category == "safety"
    assert updated_result.requires_escalation is True
    assert updated_result.assigned_team == "Drug Safety"


def test_mock_triage_regulatory_query(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    result = triage_query(
        "Site 110 needs an IRB amendment reviewed."
    )

    assert result.category == "regulatory"
    assert result.requires_escalation is True
    assert result.assigned_team == "Regulatory Affairs"
    assert result.draft_response


def test_mock_triage_safety_query(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")

    result = triage_query(
        "Site 109 reported a serious adverse event."
    )

    assert result.category == "safety"
    assert result.requires_escalation is True
    assert result.assigned_team == "Drug Safety"

def test_sae_does_not_match_inside_another_word():
    result = TriageResult(
        category="logistics",
        requires_escalation=False,
        assigned_team="Site Logistics",
        draft_response="Thank you for your inquiry.",
    )

    updated_result = enforce_safety_escalation(
        "Site 110 is checking shipment reference SAE123.",
        result,
    )

    assert updated_result.category == "logistics"
    assert updated_result.requires_escalation is False
    assert updated_result.assigned_team == "Site Logistics"


def test_sae_with_punctuation_triggers_escalation():
    result = TriageResult(
        category="logistics",
        requires_escalation=False,
        assigned_team="Site Logistics",
        draft_response="Thank you for your inquiry.",
    )

    updated_result = enforce_safety_escalation(
        "Site 109 reported an SAE; please advise.",
        result,
    )

    assert updated_result.category == "safety"
    assert updated_result.requires_escalation is True
    assert updated_result.assigned_team == "Drug Safety"
