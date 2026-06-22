"""Dataclass schema for a DVA-C02 concept record."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Concept:
    """A human-editable concept record grounded in official AWS material.

    Attributes
    ----------
    id:
        Stable kebab-case identifier unique within the exam (e.g. "deploy-codepipeline").
    domain:
        DVA-C02 domain name, e.g. "Deployment".
    task_statement:
        Free text of the relevant AWS exam task statement this concept supports.
    lesson_reference:
        Internal source reference (e.g. a Skill Builder lesson slug or an
        internal lesson ID). May be empty string.
    facts:
        Between 2 and 4 grounded factual statements about this concept, drawn
        from official AWS docs or verified lesson transcripts.  Empty list
        or list outside [2,4] fails the quality gate.
    traps:
        At least one common misconception or exam trap associated with this
        concept.  Empty list fails the quality gate.
    expected_answer_criteria:
        Structured string describing what the evaluator should look for in a
        correct answer.  Must be non-empty and non-blank.
    official_docs:
        At least one valid HTTPS URL pointing to official AWS documentation.
        Empty list fails the quality gate.
    skill_builder_links:
        Optional list of Skill Builder, Builder Lab, or SimuLearn URLs.  May
        be an empty list.
    lab_links:
        Optional list of lab URLs.  May be an empty list.
    ready:
        Boolean gate.  Records with ready=False are excluded from runtime
        helpers unless explicitly requested.
    """

    id: str
    domain: str
    task_statement: str
    facts: list[str] = field(default_factory=list)
    traps: list[str] = field(default_factory=list)
    expected_answer_criteria: str = ""
    official_docs: list[str] = field(default_factory=list)
    skill_builder_links: list[str] = field(default_factory=list)
    lab_links: list[str] = field(default_factory=list)
    lesson_reference: str = ""
    ready: bool = False

    # -------------------------------------------------------------------------
    # Derived helpers
    # -------------------------------------------------------------------------
    @property
    def trap_count(self) -> int:
        return len(self.traps)

    @property
    def fact_count(self) -> int:
        return len(self.facts)

    @property
    def official_docs_count(self) -> int:
        return len(self.official_docs)
