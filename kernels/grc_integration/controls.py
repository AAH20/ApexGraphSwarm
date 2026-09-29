"""Control definitions and cross-framework mapping for GRC compliance."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ControlFramework(enum.Enum):
    """Supported compliance frameworks."""

    ISO_42001 = "ISO42001"
    SOC2 = "SOC2"
    PCI_DSS = "PCI_DSS"
    DORA = "DORA"
    SEC_8K = "SEC_8K"
    FFIEC_CAT = "FFIEC_CAT"


class ControlStatus(enum.Enum):
    """Implementation status of a control."""

    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    IMPLEMENTED = "implemented"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Control:
    """A single compliance control definition.

    Attributes:
        control_id: Unique identifier (e.g., "ISO42001-A.6.1").
        framework: The compliance framework this control belongs to.
        title: Short human-readable title.
        description: Detailed description of the control requirement.
        category: Control category (e.g., "Access Control", "Risk Assessment").
        status: Current implementation status.
        evidence_ids: List of evidence IDs supporting this control.
        metadata: Additional framework-specific metadata.
    """

    control_id: str
    framework: ControlFramework
    title: str
    description: str
    category: str
    status: ControlStatus = ControlStatus.NOT_IMPLEMENTED
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "controlId": self.control_id,
            "framework": self.framework.value,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "status": self.status.value,
            "evidenceIds": list(self.evidence_ids),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Control:
        return cls(
            control_id=d["controlId"],
            framework=ControlFramework(d["framework"]),
            title=d["title"],
            description=d["description"],
            category=d["category"],
            status=ControlStatus(d.get("status", "not_implemented")),
            evidence_ids=list(d.get("evidenceIds", [])),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass
class ControlMapping:
    """Maps a control to equivalent controls in other frameworks.

    Attributes:
        source_control_id: The source control ID.
        source_framework: The source framework.
        mappings: List of (framework, control_id) tuples for equivalent controls.
    """

    source_control_id: str
    source_framework: ControlFramework
    mappings: list[tuple[ControlFramework, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceControlId": self.source_control_id,
            "sourceFramework": self.source_framework.value,
            "mappings": [
                {"framework": fw.value, "controlId": cid}
                for fw, cid in self.mappings
            ],
        }


class ControlRegistry:
    """Registry of all compliance controls with cross-framework mapping."""

    def __init__(self) -> None:
        self._controls: dict[str, Control] = {}
        self._mappings: dict[str, ControlMapping] = {}

    def register(self, control: Control) -> Control:
        """Register a control definition."""
        self._controls[control.control_id] = control
        return control

    def get(self, control_id: str) -> Control | None:
        """Retrieve a control by ID."""
        return self._controls.get(control_id)

    def list_by_framework(self, framework: ControlFramework) -> list[Control]:
        """List all controls for a given framework."""
        return [c for c in self._controls.values() if c.framework == framework]

    def list_by_category(self, category: str) -> list[Control]:
        """List all controls in a given category."""
        return [c for c in self._controls.values() if c.category == category]

    def add_mapping(self, mapping: ControlMapping) -> None:
        """Add a cross-framework control mapping."""
        self._mappings[mapping.source_control_id] = mapping

    def get_mappings(self, control_id: str) -> list[tuple[ControlFramework, str]]:
        """Get cross-framework mappings for a control."""
        mapping = self._mappings.get(control_id)
        return mapping.mappings if mapping else []

    def coverage_summary(self) -> dict[str, dict[str, int]]:
        """Return coverage summary by framework and status."""
        summary: dict[str, dict[str, int]] = {}
        for fw in ControlFramework:
            controls = self.list_by_framework(fw)
            summary[fw.value] = {
                "total": len(controls),
                "implemented": sum(
                    1 for c in controls
                    if c.status == ControlStatus.IMPLEMENTED
                ),
                "partiallyImplemented": sum(
                    1 for c in controls
                    if c.status == ControlStatus.PARTIALLY_IMPLEMENTED
                ),
                "notImplemented": sum(
                    1 for c in controls
                    if c.status == ControlStatus.NOT_IMPLEMENTED
                ),
                "notApplicable": sum(
                    1 for c in controls
                    if c.status == ControlStatus.NOT_APPLICABLE
                ),
            }
        return summary

    def __len__(self) -> int:
        return len(self._controls)
