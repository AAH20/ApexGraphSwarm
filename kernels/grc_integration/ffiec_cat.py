"""FFIEC CAT (Cybersecurity Assessment Tool) controls.

Defines controls for the Federal Financial Institutions Examination Council
Cybersecurity Assessment Tool, covering cyber risk management and oversight,
threat intelligence and collaboration, cybersecurity controls, external
dependency management, and cyber incident management and resilience.
"""
from __future__ import annotations

from .controls import Control, ControlFramework, ControlStatus


class FFIECCATControl:
    """FFIEC CAT control definitions."""

    # Domain 1: Cyber Risk Management and Oversight
    OVERSIGHT_GOVERNANCE = Control(
        control_id="FFIEC-1.1",
        framework=ControlFramework.FFIEC_CAT,
        title="Cybersecurity Governance and Oversight",
        description="The board of directors and senior management establish and maintain a cybersecurity governance framework with clearly defined roles and responsibilities.",
        category="Cyber Risk Management and Oversight",
    )

    RISK_MANAGEMENT = Control(
        control_id="FFIEC-1.2",
        framework=ControlFramework.FFIEC_CAT,
        title="Cyber Risk Management",
        description="Cyber risk management is integrated into the institution's overall risk management framework.",
        category="Cyber Risk Management and Oversight",
    )

    STRATEGY = Control(
        control_id="FFIEC-1.3",
        framework=ControlFramework.FFIEC_CAT,
        title="Cybersecurity Strategy",
        description="A cybersecurity strategy is established, approved by the board, and aligned with the institution's risk appetite.",
        category="Cyber Risk Management and Oversight",
    )

    RISK_APPETITE = Control(
        control_id="FFIEC-1.4",
        framework=ControlFramework.FFIEC_CAT,
        title="Risk Appetite and Tolerance",
        description="The board establishes and monitors cyber risk appetite and tolerance levels.",
        category="Cyber Risk Management and Oversight",
    )

    POLICIES_PROCEDURES = Control(
        control_id="FFIEC-1.5",
        framework=ControlFramework.FFIEC_CAT,
        title="Policies and Procedures",
        description="Cybersecurity policies and procedures are established, approved, and communicated to all relevant personnel.",
        category="Cyber Risk Management and Oversight",
    )

    # Domain 2: Threat Intelligence and Collaboration
    THREAT_INTELLIGENCE = Control(
        control_id="FFIEC-2.1",
        framework=ControlFramework.FFIEC_CAT,
        title="Threat Intelligence",
        description="The institution collects, analyzes, and uses threat intelligence to inform cybersecurity decisions.",
        category="Threat Intelligence and Collaboration",
    )

    INFORMATION_SHARING = Control(
        control_id="FFIEC-2.2",
        framework=ControlFramework.FFIEC_CAT,
        title="Information Sharing",
        description="The institution participates in information sharing forums and collaborates with peers and government entities.",
        category="Threat Intelligence and Collaboration",
    )

    THREAT_MONITORING = Control(
        control_id="FFIEC-2.3",
        framework=ControlFramework.FFIEC_CAT,
        title="Threat Monitoring",
        description="The institution monitors the cyber threat landscape and adjusts defenses accordingly.",
        category="Threat Intelligence and Collaboration",
    )

    # Domain 3: Cybersecurity Controls
    PREVENTIVE_CONTROLS = Control(
        control_id="FFIEC-3.1",
        framework=ControlFramework.FFIEC_CAT,
        title="Preventive Controls",
        description="The institution implements preventive controls to protect against cyber threats, including access controls, network security, and data protection.",
        category="Cybersecurity Controls",
    )

    DETECTIVE_CONTROLS = Control(
        control_id="FFIEC-3.2",
        framework=ControlFramework.FFIEC_CAT,
        title="Detective Controls",
        description="The institution implements detective controls to identify cybersecurity events in a timely manner.",
        category="Cybersecurity Controls",
    )

    ACCESS_MANAGEMENT = Control(
        control_id="FFIEC-3.3",
        framework=ControlFramework.FFIEC_CAT,
        title="Access and Identity Management",
        description="The institution implements access and identity management controls, including multi-factor authentication and least privilege.",
        category="Cybersecurity Controls",
    )

    NETWORK_SECURITY = Control(
        control_id="FFIEC-3.4",
        framework=ControlFramework.FFIEC_CAT,
        title="Network Security",
        description="The institution implements network security controls, including firewalls, intrusion detection/prevention, and segmentation.",
        category="Cybersecurity Controls",
    )

    DATA_PROTECTION = Control(
        control_id="FFIEC-3.5",
        framework=ControlFramework.FFIEC_CAT,
        title="Data Protection",
        description="The institution implements data protection controls, including encryption, data loss prevention, and secure disposal.",
        category="Cybersecurity Controls",
    )

    SECURE_DEVELOPMENT = Control(
        control_id="FFIEC-3.6",
        framework=ControlFramework.FFIEC_CAT,
        title="Secure Development Practices",
        description="The institution implements secure development practices for internally developed software and systems.",
        category="Cybersecurity Controls",
    )

    ENDPOINT_SECURITY = Control(
        control_id="FFIEC-3.7",
        framework=ControlFramework.FFIEC_CAT,
        title="Endpoint Security",
        description="The institution implements endpoint security controls, including anti-malware, host-based firewalls, and mobile device management.",
        category="Cybersecurity Controls",
    )

    # Domain 4: External Dependency Management
    THIRD_PARTY_RISK = Control(
        control_id="FFIEC-4.1",
        framework=ControlFramework.FFIEC_CAT,
        title="Third-Party Risk Management",
        description="The institution identifies, assesses, and manages risks associated with third-party relationships.",
        category="External Dependency Management",
    )

    VENDOR_DUE_DILIGENCE = Control(
        control_id="FFIEC-4.2",
        framework=ControlFramework.FFIEC_CAT,
        title="Vendor Due Diligence",
        description="The institution performs due diligence on third-party service providers before entering into contractual arrangements.",
        category="External Dependency Management",
    )

    CONTRACTUAL_REQUIREMENTS = Control(
        control_id="FFIEC-4.3",
        framework=ControlFramework.FFIEC_CAT,
        title="Contractual Security Requirements",
        description="The institution includes cybersecurity requirements in third-party contracts.",
        category="External Dependency Management",
    )

    ONGOING_MONITORING = Control(
        control_id="FFIEC-4.4",
        framework=ControlFramework.FFIEC_CAT,
        title="Ongoing Third-Party Monitoring",
        description="The institution monitors third-party service providers on an ongoing basis for compliance with security requirements.",
        category="External Dependency Management",
    )

    # Domain 5: Cyber Incident Management and Resilience
    INCIDENT_RESPONSE = Control(
        control_id="FFIEC-5.1",
        framework=ControlFramework.FFIEC_CAT,
        title="Incident Response Planning",
        description="The institution maintains and tests an incident response plan for cybersecurity events.",
        category="Cyber Incident Management and Resilience",
    )

    INCIDENT_DETECTION = Control(
        control_id="FFIEC-5.2",
        framework=ControlFramework.FFIEC_CAT,
        title="Incident Detection and Analysis",
        description="The institution detects, analyzes, and escalates cybersecurity incidents in a timely manner.",
        category="Cyber Incident Management and Resilience",
    )

    INCIDENT_REPORTING = Control(
        control_id="FFIEC-5.3",
        framework=ControlFramework.FFIEC_CAT,
        title="Incident Reporting and Communication",
        description="The institution reports cybersecurity incidents to appropriate stakeholders, including regulators and law enforcement.",
        category="Cyber Incident Management and Resilience",
    )

    BUSINESS_CONTINUITY = Control(
        control_id="FFIEC-5.4",
        framework=ControlFramework.FFIEC_CAT,
        title="Business Continuity and Disaster Recovery",
        description="The institution maintains and tests business continuity and disaster recovery plans that address cyber incidents.",
        category="Cyber Incident Management and Resilience",
    )

    RESILIENCE_TESTING = Control(
        control_id="FFIEC-5.5",
        framework=ControlFramework.FFIEC_CAT,
        title="Resilience Testing",
        description="The institution conducts resilience testing, including tabletop exercises and simulations, to validate incident response and recovery capabilities.",
        category="Cyber Incident Management and Resilience",
    )

    @classmethod
    def all_controls(cls) -> list[Control]:
        """Return all FFIEC CAT controls."""
        return [
            cls.OVERSIGHT_GOVERNANCE,
            cls.RISK_MANAGEMENT,
            cls.STRATEGY,
            cls.RISK_APPETITE,
            cls.POLICIES_PROCEDURES,
            cls.THREAT_INTELLIGENCE,
            cls.INFORMATION_SHARING,
            cls.THREAT_MONITORING,
            cls.PREVENTIVE_CONTROLS,
            cls.DETECTIVE_CONTROLS,
            cls.ACCESS_MANAGEMENT,
            cls.NETWORK_SECURITY,
            cls.DATA_PROTECTION,
            cls.SECURE_DEVELOPMENT,
            cls.ENDPOINT_SECURITY,
            cls.THIRD_PARTY_RISK,
            cls.VENDOR_DUE_DILIGENCE,
            cls.CONTRACTUAL_REQUIREMENTS,
            cls.ONGOING_MONITORING,
            cls.INCIDENT_RESPONSE,
            cls.INCIDENT_DETECTION,
            cls.INCIDENT_REPORTING,
            cls.BUSINESS_CONTINUITY,
            cls.RESILIENCE_TESTING,
        ]


class FFIEC_CAT_Domain:
    """FFIEC CAT domain assessment."""

    def __init__(self, controls: list[Control] | None = None) -> None:
        self.controls = controls or FFIECCATControl.all_controls()

    def assess(self) -> dict[str, object]:
        """Run assessment and return summary."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        na = sum(1 for c in self.controls if c.status == ControlStatus.NOT_APPLICABLE)
        return {
            "framework": "FFIEC_CAT",
            "totalControls": total,
            "implemented": implemented,
            "partiallyImplemented": partial,
            "notImplemented": not_impl,
            "notApplicable": na,
            "complianceRate": round((implemented / total) * 100, 1) if total else 0.0,
        }
