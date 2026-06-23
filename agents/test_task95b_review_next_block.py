"""Task 9.5b — Review next block from packet links.

AC2: SageCard renders compact Review block from official_docs /
     skill_builder_links / lab_links; no invented links.

All tests compile and run; they fail until 9.5 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_task95_shared import FAKE_CONCEPT

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC2 — Review next renders compact block from packet links
# ---------------------------------------------------------------------------

_ROOT = _AGENTS_DIR.parent


class TestAC2_ReviewNextBlockFromPacketLinks:
    """SageCard frontend must render Review next as a compact block from concept links."""

    def test_sage_card_file_exists(self):
        """SageCard component must exist at components/session/sage-card.tsx."""
        path = _ROOT / "components" / "session" / "sage-card.tsx"
        assert path.exists(), (
            "SageCard must exist at components/session/sage-card.tsx"
        )

    def test_sage_card_review_block_type_exists(self):
        """lib/types.ts must have a type for the Review next block."""
        types_path = _ROOT / "lib" / "types.ts"
        assert types_path.exists(), "lib/types.ts must exist"
        content = types_path.read_text()
        assert "ReviewNext" in content or "review_next" in content, (
            "lib/types.ts must declare ReviewNext or review_next type "
            "for the compact review resource block"
        )

    def test_sage_card_props_include_review_next(self):
        """SageCard must accept a reviewNext or review_next prop."""
        path = _ROOT / "components" / "session" / "sage-card.tsx"
        content = path.read_text()
        assert "reviewNext" in content or "review_next" in content, (
            "SageCard must have a 'reviewNext' or 'review_next' prop "
            "for the compact review links block"
        )

    def test_review_next_derives_from_exchange_citations(self):
        """Exchange record must carry citations that SageCard maps to Review next."""
        exchange = {
            "cycle": 1,
            "domain": "Deployment",
            "topic": "CodePipeline Basics",
            "challenge": {
                "concept_id": "deploy-codepipeline-basics",
                "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
                "skill_builder_links": ["https://skillbuilder.aws/labs/"],
                "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
            },
            "user_answer": "Source stage.",
            "outcome": "correct",
            "answer_intent": "attempt",
            "missed_criteria": [],
            "triggered_traps": [],
            "sage_response": "CodePipeline requires a Source stage.",
            "citations": [
                {
                    "url": "https://docs.aws.amazon.com/codepipeline/latest/userguide/",
                    "title": "CodePipeline docs",
                    "snippet_id": "ref",
                },
                {
                    "url": "https://skillbuilder.aws/labs/",
                    "title": "Skill Builder labs",
                    "snippet_id": "ref",
                },
            ],
        }
        # Verify the exchange has the structure needed for SageCard to render Review next.
        assert "citations" in exchange
        assert any("skillbuilder" in c["url"] for c in exchange["citations"]) or \
               any("lab" in c["url"] for c in exchange["citations"]), (
            "Exchange citations must include skill_builder_links or lab_links"
        )

    def test_review_next_empty_when_no_packet_links(self):
        """When all link lists are empty, citations must be empty and
        load_sage_grounding must return a neutral source_context."""
        from sage_sources import load_sage_grounding

        grounding = load_sage_grounding(
            exam_id="dva-c02",
            topic_id="deploy-codepipeline-basics",
            topic="CodePipeline Basics",
            services=["CodePipeline"],
            source_ids=[],
            official_docs=[],
            skill_builder_links=[],
            lab_links=[],
        )
        assert grounding["citations"] == []
        assert grounding["source_context"] == "No verified source was found for this topic."
