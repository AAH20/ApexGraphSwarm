"""ISO/IEC 42001:2023 AI Management System controls.

Defines the core controls for ISO 42001 compliance, covering AI system
lifecycle management, risk assessment, and governance.
"""
from __future__ import annotations

from .controls import Control, ControlFramework, ControlStatus


class ISO42001Control:
    """ISO/IEC 42001:2023 control definitions."""

    # Clause 4: Context of the organization
    ORGANIZATIONAL_CONTEXT = Control(
        control_id="ISO42001-4.1",
        framework=ControlFramework.ISO_42001,
        title="Understanding the organization and its context",
        description="Determine external and internal issues relevant to the AI management system purpose and strategic direction.",
        category="Context",
    )

    NEEDS_AND_EXPECTATIONS = Control(
        control_id="ISO42001-4.2",
        framework=ControlFramework.ISO_42001,
        title="Understanding the needs and expectations of interested parties",
        description="Determine interested parties and their relevant requirements for the AI management system.",
        category="Context",
    )

    SCOPE = Control(
        control_id="ISO42001-4.3",
        framework=ControlFramework.ISO_42001,
        title="Determining the scope of the AI management system",
        description="Define the boundaries and applicability of the AI management system.",
        category="Context",
    )

    AI_MANAGEMENT_SYSTEM = Control(
        control_id="ISO42001-4.4",
        framework=ControlFramework.ISO_42001,
        title="AI management system",
        description="Establish, implement, maintain, and continually improve an AI management system.",
        category="Context",
    )

    # Clause 5: Leadership
    LEADERSHIP_COMMITMENT = Control(
        control_id="ISO42001-5.1",
        framework=ControlFramework.ISO_42001,
        title="Leadership and commitment",
        description="Top management shall demonstrate leadership and commitment with respect to the AI management system.",
        category="Leadership",
    )

    AI_POLICY = Control(
        control_id="ISO42001-5.2",
        framework=ControlFramework.ISO_42001,
        title="AI policy",
        description="Establish an AI policy that is appropriate to the purpose of the organization and provides a framework for setting AI objectives.",
        category="Leadership",
    )

    ROLES_RESPONSIBILITIES = Control(
        control_id="ISO42001-5.3",
        framework=ControlFramework.ISO_42001,
        title="Organizational roles, responsibilities and authorities",
        description="Assign and communicate roles, responsibilities, and authorities for the AI management system.",
        category="Leadership",
    )

    # Clause 6: Planning
    RISK_ASSESSMENT = Control(
        control_id="ISO42001-6.1",
        framework=ControlFramework.ISO_42001,
        title="Actions to address risks and opportunities",
        description="Plan actions to address risks and opportunities for the AI management system, including AI-specific risks.",
        category="Planning",
    )

    AI_OBJECTIVES = Control(
        control_id="ISO42001-6.2",
        framework=ControlFramework.ISO_42001,
        title="AI objectives and planning to achieve them",
        description="Establish AI objectives at relevant functions and levels, and plan to achieve them.",
        category="Planning",
    )

    # Clause 7: Support
    RESOURCES = Control(
        control_id="ISO42001-7.1",
        framework=ControlFramework.ISO_42001,
        title="Resources",
        description="Determine and provide the resources needed for the establishment, implementation, maintenance, and continual improvement of the AI management system.",
        category="Support",
    )

    COMPETENCE = Control(
        control_id="ISO42001-7.2",
        framework=ControlFramework.ISO_42001,
        title="Competence",
        description="Determine the necessary competence of persons doing work under the organization's control that affects AI system performance.",
        category="Support",
    )

    AWARENESS = Control(
        control_id="ISO42001-7.3",
        framework=ControlFramework.ISO_42001,
        title="Awareness",
        description="Ensure persons doing work under the organization's control are aware of the AI policy, AI objectives, and their contribution to the AI management system.",
        category="Support",
    )

    COMMUNICATION = Control(
        control_id="ISO42001-7.4",
        framework=ControlFramework.ISO_42001,
        title="Communication",
        description="Determine the internal and external communications relevant to the AI management system.",
        category="Support",
    )

    DOCUMENTED_INFORMATION = Control(
        control_id="ISO42001-7.5",
        framework=ControlFramework.ISO_42001,
        title="Documented information",
        description="Maintain and control documented information required by the AI management system and by the standard.",
        category="Support",
    )

    # Clause 8: Operation
    OPERATIONAL_PLANNING = Control(
        control_id="ISO42001-8.1",
        framework=ControlFramework.ISO_42001,
        title="Operational planning and control",
        description="Plan, implement, and control the processes needed to meet AI management system requirements.",
        category="Operation",
    )

    AI_RISK_ASSESSMENT = Control(
        control_id="ISO42001-8.2",
        framework=ControlFramework.ISO_42001,
        title="AI risk assessment",
        description="Perform AI-specific risk assessment considering the AI system lifecycle, data quality, and potential impacts.",
        category="Operation",
    )

    AI_RISK_TREATMENT = Control(
        control_id="ISO42001-8.3",
        framework=ControlFramework.ISO_42001,
        title="AI risk treatment",
        description="Implement risk treatment plans for AI-specific risks, including mitigation measures and controls.",
        category="Operation",
    )

    # Clause 9: Performance evaluation
    MONITORING_MEASUREMENT = Control(
        control_id="ISO42001-9.1",
        framework=ControlFramework.ISO_42001,
        title="Monitoring, measurement, analysis and evaluation",
        description="Monitor, measure, analyze, and evaluate the AI management system and AI system performance.",
        category="Performance",
    )

    INTERNAL_AUDIT = Control(
        control_id="ISO42001-9.2",
        framework=ControlFramework.ISO_42001,
        title="Internal audit",
        description="Conduct internal audits at planned intervals to provide information on whether the AI management system conforms to requirements.",
        category="Performance",
    )

    MANAGEMENT_REVIEW = Control(
        control_id="ISO42001-9.3",
        framework=ControlFramework.ISO_42001,
        title="Management review",
        description="Top management shall review the AI management system at planned intervals to ensure its continuing suitability, adequacy, and effectiveness.",
        category="Performance",
    )

    # Clause 10: Improvement
    NONCONFORMITY_CORRECTIVE_ACTION = Control(
        control_id="ISO42001-10.1",
        framework=ControlFramework.ISO_42001,
        title="Nonconformity and corrective action",
        description="React to nonconformities, take action to control and correct them, and deal with the consequences.",
        category="Improvement",
    )

    CONTINUAL_IMPROVEMENT = Control(
        control_id="ISO42001-10.2",
        framework=ControlFramework.ISO_42001,
        title="Continual improvement",
        description="Continually improve the suitability, adequacy, and effectiveness of the AI management system.",
        category="Improvement",
    )

    @classmethod
    def all_controls(cls) -> list[Control]:
        """Return all ISO 42001 controls."""
        return [
            cls.ORGANIZATIONAL_CONTEXT,
            cls.NEEDS_AND_EXPECTATIONS,
            cls.SCOPE,
            cls.AI_MANAGEMENT_SYSTEM,
            cls.LEADERSHIP_COMMITMENT,
            cls.AI_POLICY,
            cls.ROLES_RESPONSIBILITIES,
            cls.RISK_ASSESSMENT,
            cls.AI_OBJECTIVES,
            cls.RESOURCES,
            cls.COMPETENCE,
            cls.AWARENESS,
            cls.COMMUNICATION,
            cls.DOCUMENTED_INFORMATION,
            cls.OPERATIONAL_PLANNING,
            cls.AI_RISK_ASSESSMENT,
            cls.AI_RISK_TREATMENT,
            cls.MONITORING_MEASUREMENT,
            cls.INTERNAL_AUDIT,
            cls.MANAGEMENT_REVIEW,
            cls.NONCONFORMITY_CORRECTIVE_ACTION,
            cls.CONTINUAL_IMPROVEMENT,
        ]


class ISO42001Assessment:
    """ISO 42001 compliance assessment."""

    def __init__(self, controls: list[Control] | None = None) -> None:
        self.controls = controls or ISO42001Control.all_controls()

    def assess(self) -> dict[str, object]:
        """Run assessment and return summary."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        na = sum(1 for c in self.controls if c.status == ControlStatus.NOT_APPLICABLE)
        return {
            "framework": "ISO42001",
            "totalControls": total,
            "implemented": implemented,
            "partiallyImplemented": partial,
            "notImplemented": not_impl,
            "notApplicable": na,
            "complianceRate": round((implemented / total) * 100, 1) if total else 0.0,
        }
