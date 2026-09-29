"""EU DORA (Digital Operational Resilience Act) controls.

Defines controls for the European Union's DORA regulation, covering ICT risk
management, incident reporting, digital operational resilience testing, and
ICT third-party risk management.
"""
from __future__ import annotations

from .controls import Control, ControlFramework, ControlStatus


class DORAControl:
    """EU DORA control definitions."""

    # Title I: General Provisions
    GOVERNANCE = Control(
        control_id="DORA-1.1",
        framework=ControlFramework.DORA,
        title="ICT risk management framework",
        description="Financial entities shall have in place an internal ICT risk management framework as part of their overall risk management system.",
        category="Governance",
    )

    ICT_RISK_MANAGEMENT = Control(
        control_id="DORA-1.2",
        framework=ControlFramework.DORA,
        title="ICT risk management policies and procedures",
        description="Financial entities shall define, approve, and review ICT risk management policies and procedures.",
        category="Governance",
    )

    # Title II: ICT Risk Management
    ICT_RISK_FRAMEWORK = Control(
        control_id="DORA-2.1",
        framework=ControlFramework.DORA,
        title="ICT risk management framework components",
        description="The ICT risk management framework shall include strategies, policies, procedures, ICT tools, and competent staff.",
        category="ICT Risk Management",
    )

    IDENTIFICATION = Control(
        control_id="DORA-2.2",
        framework=ControlFramework.DORA,
        title="Identification of ICT risks",
        description="Financial entities shall identify, classify, and adequately document all ICT risks.",
        category="ICT Risk Management",
    )

    PROTECTION = Control(
        control_id="DORA-2.3",
        framework=ControlFramework.DORA,
        title="Protection and prevention measures",
        description="Financial entities shall implement policies, procedures, protocols, and tools to protect ICT systems from damage and unauthorized access.",
        category="ICT Risk Management",
    )

    DETECTION = Control(
        control_id="DORA-2.4",
        framework=ControlFramework.DORA,
        title="Detection mechanisms",
        description="Financial entities shall implement mechanisms to promptly detect anomalous activities.",
        category="ICT Risk Management",
    )

    RESPONSE = Control(
        control_id="DORA-2.5",
        framework=ControlFramework.DORA,
        title="Response and recovery plans",
        description="Financial entities shall implement response and recovery plans for ICT-related incidents.",
        category="ICT Risk Management",
    )

    LEARNING = Control(
        control_id="DORA-2.6",
        framework=ControlFramework.DORA,
        title="Learning and evolving",
        description="Financial entities shall learn from ICT-related incidents and update their ICT risk management framework accordingly.",
        category="ICT Risk Management",
    )

    # Title III: ICT-Related Incident Management
    INCIDENT_MANAGEMENT = Control(
        control_id="DORA-3.1",
        framework=ControlFramework.DORA,
        title="ICT-related incident management process",
        description="Financial entities shall define, establish, and implement an ICT-related incident management process.",
        category="Incident Management",
    )

    INCIDENT_CLASSIFICATION = Control(
        control_id="DORA-3.2",
        framework=ControlFramework.DORA,
        title="ICT-related incident classification",
        description="Financial entities shall classify ICT-related incidents according to criteria defined in the regulation.",
        category="Incident Management",
    )

    MAJOR_INCIDENT_REPORTING = Control(
        control_id="DORA-3.3",
        framework=ControlFramework.DORA,
        title="Major ICT-related incident reporting",
        description="Financial entities shall report major ICT-related incidents to competent authorities.",
        category="Incident Management",
    )

    INCIDENT_REPORTING_TIMELINE = Control(
        control_id="DORA-3.4",
        framework=ControlFramework.DORA,
        title="Incident reporting timeline",
        description="Financial entities shall submit initial notification, intermediate report, final report, and voluntary meaningful updates within defined timelines.",
        category="Incident Management",
    )

    # Title IV: Digital Operational Resilience Testing
    TESTING_PROGRAM = Control(
        control_id="DORA-4.1",
        framework=ControlFramework.DORA,
        title="Digital operational resilience testing programme",
        description="Financial entities shall establish, maintain, and review a digital operational resilience testing programme.",
        category="Resilience Testing",
    )

    THREAT_LED_PENETRATION_TESTING = Control(
        control_id="DORA-4.2",
        framework=ControlFramework.DORA,
        title="Threat-led penetration testing",
        description="Financial entities shall perform threat-led penetration testing at least every three years.",
        category="Resilience Testing",
    )

    TESTING_SCOPE = Control(
        control_id="DORA-4.3",
        framework=ControlFramework.DORA,
        title="Testing scope and methodology",
        description="Testing shall cover all ICT systems and services that support critical or important functions.",
        category="Resilience Testing",
    )

    TESTING_REMEDIATION = Control(
        control_id="DORA-4.4",
        framework=ControlFramework.DORA,
        title="Testing remediation",
        description="Financial entities shall remediate issues identified through testing in a timely manner.",
        category="Resilience Testing",
    )

    # Title V: ICT Third-Party Risk Management
    THIRD_PARTY_RISK = Control(
        control_id="DORA-5.1",
        framework=ControlFramework.DORA,
        title="ICT third-party risk management framework",
        description="Financial entities shall manage ICT third-party risk through a comprehensive framework.",
        category="Third-Party Risk",
    )

    THIRD_PARTY_REGISTER = Control(
        control_id="DORA-5.2",
        framework=ControlFramework.DORA,
        title="Register of information",
        description="Financial entities shall maintain and update a register of information regarding all ICT third-party contractual arrangements.",
        category="Third-Party Risk",
    )

    THIRD_PARTY_ASSESSMENT = Control(
        control_id="DORA-5.3",
        framework=ControlFramework.DORA,
        title="ICT third-party risk assessment",
        description="Financial entities shall assess ICT third-party risk before entering into contractual arrangements.",
        category="Third-Party Risk",
    )

    THIRD_PARTY_CONTRACT = Control(
        control_id="DORA-5.4",
        framework=ControlFramework.DORA,
        title="ICT third-party contractual arrangements",
        description="Financial entities shall include specific provisions in ICT third-party contractual arrangements.",
        category="Third-Party Risk",
    )

    CRITICAL_THIRD_PARTY = Control(
        control_id="DORA-5.5",
        framework=ControlFramework.DORA,
        title="Critical ICT third-party providers",
        description="Financial entities shall subject critical ICT third-party providers to enhanced oversight.",
        category="Third-Party Risk",
    )

    # Title VI: Information Sharing
    INFORMATION_SHARING = Control(
        control_id="DORA-6.1",
        framework=ControlFramework.DORA,
        title="Information sharing arrangements",
        description="Financial entities may exchange information and intelligence on cyber threats and vulnerabilities.",
        category="Information Sharing",
    )

    # Title VII: Competent Authorities
    COMPETENT_AUTHORITIES = Control(
        control_id="DORA-7.1",
        framework=ControlFramework.DORA,
        title="Competent authorities oversight",
        description="Competent authorities shall supervise financial entities' compliance with DORA requirements.",
        category="Oversight",
    )

    @classmethod
    def all_controls(cls) -> list[Control]:
        """Return all DORA controls."""
        return [
            cls.GOVERNANCE,
            cls.ICT_RISK_MANAGEMENT,
            cls.ICT_RISK_FRAMEWORK,
            cls.IDENTIFICATION,
            cls.PROTECTION,
            cls.DETECTION,
            cls.RESPONSE,
            cls.LEARNING,
            cls.INCIDENT_MANAGEMENT,
            cls.INCIDENT_CLASSIFICATION,
            cls.MAJOR_INCIDENT_REPORTING,
            cls.INCIDENT_REPORTING_TIMELINE,
            cls.TESTING_PROGRAM,
            cls.THREAT_LED_PENETRATION_TESTING,
            cls.TESTING_SCOPE,
            cls.TESTING_REMEDIATION,
            cls.THIRD_PARTY_RISK,
            cls.THIRD_PARTY_REGISTER,
            cls.THIRD_PARTY_ASSESSMENT,
            cls.THIRD_PARTY_CONTRACT,
            cls.CRITICAL_THIRD_PARTY,
            cls.INFORMATION_SHARING,
            cls.COMPETENT_AUTHORITIES,
        ]


class DORARegulation:
    """EU DORA compliance assessment."""

    def __init__(self, controls: list[Control] | None = None) -> None:
        self.controls = controls or DORAControl.all_controls()

    def assess(self) -> dict[str, object]:
        """Run assessment and return summary."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        na = sum(1 for c in self.controls if c.status == ControlStatus.NOT_APPLICABLE)
        return {
            "framework": "DORA",
            "totalControls": total,
            "implemented": implemented,
            "partiallyImplemented": partial,
            "notImplemented": not_impl,
            "notApplicable": na,
            "complianceRate": round((implemented / total) * 100, 1) if total else 0.0,
        }
