"""SOC 2 Trust Service Criteria controls.

Defines controls for the AICPA SOC 2 Trust Services Criteria: Security,
Availability, Processing Integrity, Confidentiality, and Privacy.
"""
from __future__ import annotations

from .controls import Control, ControlFramework, ControlStatus


class SOC2Control:
    """SOC 2 Trust Service Criteria control definitions."""

    # Common Criteria (CC)
    CC1_1 = Control(
        control_id="SOC2-CC1.1",
        framework=ControlFramework.SOC2,
        title="Control Environment",
        description="The entity demonstrates a commitment to integrity and ethical values.",
        category="Common Criteria",
    )

    CC1_2 = Control(
        control_id="SOC2-CC1.2",
        framework=ControlFramework.SOC2,
        title="Oversight Responsibility",
        description="The board of directors demonstrates independence from management and exercises oversight.",
        category="Common Criteria",
    )

    CC2_1 = Control(
        control_id="SOC2-CC2.1",
        framework=ControlFramework.SOC2,
        title="Communication and Information",
        description="The entity internally communicates information to support the functioning of internal control.",
        category="Common Criteria",
    )

    CC3_1 = Control(
        control_id="SOC2-CC3.1",
        framework=ControlFramework.SOC2,
        title="Risk Assessment Process",
        description="The entity specifies objectives with sufficient clarity to enable the identification and assessment of risks.",
        category="Common Criteria",
    )

    CC4_1 = Control(
        control_id="SOC2-CC4.1",
        framework=ControlFramework.SOC2,
        title="Monitoring Activities",
        description="The entity selects, develops, and performs ongoing and separate evaluations to ascertain whether components of internal control are present and functioning.",
        category="Common Criteria",
    )

    CC5_1 = Control(
        control_id="SOC2-CC5.1",
        framework=ControlFramework.SOC2,
        title="Control Activities",
        description="The entity selects and develops control activities that contribute to the mitigation of risks.",
        category="Common Criteria",
    )

    # Security Criteria (SC)
    SC6_1 = Control(
        control_id="SOC2-SC6.1",
        framework=ControlFramework.SOC2,
        title="Logical and Physical Access Controls",
        description="The entity implements logical access security software, infrastructure, and architectures over protected information assets.",
        category="Security",
    )

    SC6_2 = Control(
        control_id="SOC2-SC6.2",
        framework=ControlFramework.SOC2,
        title="User Access Provisioning and Deprovisioning",
        description="The entity authorizes, modifies, or removes access to data, software, functions, and other protected information assets.",
        category="Security",
    )

    SC6_3 = Control(
        control_id="SOC2-SC6.3",
        framework=ControlFramework.SOC2,
        title="User Access Review",
        description="The entity reviews user access rights and privileges to determine whether they are appropriate.",
        category="Security",
    )

    SC7_1 = Control(
        control_id="SOC2-SC7.1",
        framework=ControlFramework.SOC2,
        title="Infrastructure and Software Protection",
        description="The entity restricts physical access to infrastructure and software.",
        category="Security",
    )

    SC7_2 = Control(
        control_id="SOC2-SC7.2",
        framework=ControlFramework.SOC2,
        title="Malware Protection",
        description="The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software.",
        category="Security",
    )

    SC7_3 = Control(
        control_id="SOC2-SC7.3",
        framework=ControlFramework.SOC2,
        title="Network Security Controls",
        description="The entity uses boundary protection mechanisms and network segmentation.",
        category="Security",
    )

    SC7_4 = Control(
        control_id="SOC2-SC7.4",
        framework=ControlFramework.SOC2,
        title="Data Transmission Protection",
        description="The entity protects the confidentiality and integrity of information during transmission.",
        category="Security",
    )

    SC7_5 = Control(
        control_id="SOC2-SC7.5",
        framework=ControlFramework.SOC2,
        title="Data Storage Protection",
        description="The entity protects the confidentiality and integrity of information during storage.",
        category="Security",
    )

    SC8_1 = Control(
        control_id="SOC2-SC8.1",
        framework=ControlFramework.SOC2,
        title="Change Management",
        description="The entity authorizes, designs, develops or acquires, configures, documents, tests, approves, and implements changes to infrastructure, data, software, and procedures.",
        category="Security",
    )

    SC9_1 = Control(
        control_id="SOC2-SC9.1",
        framework=ControlFramework.SOC2,
        title="Risk Mitigation",
        description="The entity identifies, selects, and develops risk mitigation activities for risks arising from potential business disruptions.",
        category="Security",
    )

    # Availability Criteria (AC)
    AC1_1 = Control(
        control_id="SOC2-AC1.1",
        framework=ControlFramework.SOC2,
        title="Availability Monitoring",
        description="The entity monitors the availability of system components and services.",
        category="Availability",
    )

    AC2_1 = Control(
        control_id="SOC2-AC2.1",
        framework=ControlFramework.SOC2,
        title="Capacity Planning",
        description="The entity assesses processing capacity and system performance to meet availability objectives.",
        category="Availability",
    )

    # Processing Integrity Criteria (PI)
    PI1_1 = Control(
        control_id="SOC2-PI1.1",
        framework=ControlFramework.SOC2,
        title="Processing Integrity Monitoring",
        description="The entity monitors processing to ensure completeness, accuracy, and timeliness.",
        category="Processing Integrity",
    )

    PI1_2 = Control(
        control_id="SOC2-PI1.2",
        framework=ControlFramework.SOC2,
        title="Data Quality",
        description="The entity defines and implements policies and procedures to ensure data quality.",
        category="Processing Integrity",
    )

    # Confidentiality Criteria (CO)
    CO1_1 = Control(
        control_id="SOC2-CO1.1",
        framework=ControlFramework.SOC2,
        title="Confidential Information Identification",
        description="The entity identifies and designates confidential information to be protected.",
        category="Confidentiality",
    )

    CO1_2 = Control(
        control_id="SOC2-CO1.2",
        framework=ControlFramework.SOC2,
        title="Confidential Information Protection",
        description="The entity protects confidential information during its lifecycle.",
        category="Confidentiality",
    )

    CO1_3 = Control(
        control_id="SOC2-CO1.3",
        framework=ControlFramework.SOC2,
        title="Confidential Information Disposal",
        description="The entity disposes of confidential information when no longer needed.",
        category="Confidentiality",
    )

    # Privacy Criteria (PR)
    PR1_1 = Control(
        control_id="SOC2-PR1.1",
        framework=ControlFramework.SOC2,
        title="Privacy Notice",
        description="The entity provides notice to data subjects about its privacy practices.",
        category="Privacy",
    )

    PR2_1 = Control(
        control_id="SOC2-PR2.1",
        framework=ControlFramework.SOC2,
        title="Consent and Choice",
        description="The entity communicates choices to data subjects and obtains consent.",
        category="Privacy",
    )

    PR3_1 = Control(
        control_id="SOC2-PR3.1",
        framework=ControlFramework.SOC2,
        title="Data Collection Limitation",
        description="The entity collects personal information only for the purposes identified in the privacy notice.",
        category="Privacy",
    )

    PR4_1 = Control(
        control_id="SOC2-PR4.1",
        framework=ControlFramework.SOC2,
        title="Data Use and Retention",
        description="The entity limits the use and retention of personal information to the purposes identified.",
        category="Privacy",
    )

    PR5_1 = Control(
        control_id="SOC2-PR5.1",
        framework=ControlFramework.SOC2,
        title="Data Access and Correction",
        description="The entity provides data subjects with access to their personal information for review and correction.",
        category="Privacy",
    )

    PR6_1 = Control(
        control_id="SOC2-PR6.1",
        framework=ControlFramework.SOC2,
        title="Data Disclosure",
        description="The entity discloses personal information to third parties only for the purposes identified.",
        category="Privacy",
    )

    PR7_1 = Control(
        control_id="SOC2-PR7.1",
        framework=ControlFramework.SOC2,
        title="Data Security",
        description="The entity protects personal information against unauthorized access.",
        category="Privacy",
    )

    PR8_1 = Control(
        control_id="SOC2-PR8.1",
        framework=ControlFramework.SOC2,
        title="Data Quality and Integrity",
        description="The entity maintains accurate, complete, and relevant personal information.",
        category="Privacy",
    )

    PR9_1 = Control(
        control_id="SOC2-PR9.1",
        framework=ControlFramework.SOC2,
        title="Data Disposal",
        description="The entity disposes of personal information when no longer needed.",
        category="Privacy",
    )

    @classmethod
    def all_controls(cls) -> list[Control]:
        """Return all SOC 2 controls."""
        return [
            cls.CC1_1, cls.CC1_2, cls.CC2_1, cls.CC3_1, cls.CC4_1, cls.CC5_1,
            cls.SC6_1, cls.SC6_2, cls.SC6_3, cls.SC7_1, cls.SC7_2, cls.SC7_3,
            cls.SC7_4, cls.SC7_5, cls.SC8_1, cls.SC9_1,
            cls.AC1_1, cls.AC2_1,
            cls.PI1_1, cls.PI1_2,
            cls.CO1_1, cls.CO1_2, cls.CO1_3,
            cls.PR1_1, cls.PR2_1, cls.PR3_1, cls.PR4_1, cls.PR5_1,
            cls.PR6_1, cls.PR7_1, cls.PR8_1, cls.PR9_1,
        ]


class SOC2TrustServiceCriteria:
    """SOC 2 Trust Service Criteria assessment."""

    def __init__(self, controls: list[Control] | None = None) -> None:
        self.controls = controls or SOC2Control.all_controls()

    def assess(self) -> dict[str, object]:
        """Run assessment and return summary."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        na = sum(1 for c in self.controls if c.status == ControlStatus.NOT_APPLICABLE)
        return {
            "framework": "SOC2",
            "totalControls": total,
            "implemented": implemented,
            "partiallyImplemented": partial,
            "notImplemented": not_impl,
            "notApplicable": na,
            "complianceRate": round((implemented / total) * 100, 1) if total else 0.0,
        }
