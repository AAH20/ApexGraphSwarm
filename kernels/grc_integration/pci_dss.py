"""PCI DSS v4.0 controls.

Defines controls for the Payment Card Industry Data Security Standard v4.0,
covering cardholder data protection, network security, and access control.
"""
from __future__ import annotations

from .controls import Control, ControlFramework, ControlStatus


class PCIDSSControl:
    """PCI DSS v4.0 control definitions."""

    # Requirement 1: Install and maintain network security controls
    REQ_1_1 = Control(
        control_id="PCI-1.1",
        framework=ControlFramework.PCI_DSS,
        title="Network security controls (NSCs) are configured and maintained",
        description="NSCs are implemented and maintained to protect the cardholder data environment.",
        category="Network Security",
    )

    REQ_1_2 = Control(
        control_id="PCI-1.2",
        framework=ControlFramework.PCI_DSS,
        title="Network security controls between trusted and untrusted networks",
        description="NSCs are implemented between trusted and untrusted networks.",
        category="Network Security",
    )

    REQ_1_3 = Control(
        control_id="PCI-1.3",
        framework=ControlFramework.PCI_DSS,
        title="Network security controls for wireless environments",
        description="Specific controls are implemented for wireless environments.",
        category="Network Security",
    )

    REQ_1_4 = Control(
        control_id="PCI-1.4",
        framework=ControlFramework.PCI_DSS,
        title="Network security controls for personal firewall software",
        description="Personal firewall software is installed and active on portable computing devices.",
        category="Network Security",
    )

    # Requirement 2: Apply secure configurations to all system components
    REQ_2_1 = Control(
        control_id="PCI-2.1",
        framework=ControlFramework.PCI_DSS,
        title="Vendor-supplied defaults are changed",
        description="Vendor-supplied defaults are changed and unnecessary default accounts are removed or disabled.",
        category="Secure Configuration",
    )

    REQ_2_2 = Control(
        control_id="PCI-2.2",
        framework=ControlFramework.PCI_DSS,
        title="System components are configured securely",
        description="System components are configured securely and consistently with industry-accepted hardening standards.",
        category="Secure Configuration",
    )

    REQ_2_3 = Control(
        control_id="PCI-2.3",
        framework=ControlFramework.PCI_DSS,
        title="Wireless environments are configured securely",
        description="Wireless environments are configured securely with industry-accepted practices.",
        category="Secure Configuration",
    )

    # Requirement 3: Protect stored account data
    REQ_3_1 = Control(
        control_id="PCI-3.1",
        framework=ControlFramework.PCI_DSS,
        title="Sensitive authentication data is not stored after authorization",
        description="Sensitive authentication data (SAD) is not stored after authorization, even if encrypted.",
        category="Data Protection",
    )

    REQ_3_2 = Control(
        control_id="PCI-3.2",
        framework=ControlFramework.PCI_DSS,
        title="Full track data is not stored",
        description="Full track data (magnetic-stripe data or equivalent) is not stored after authorization.",
        category="Data Protection",
    )

    REQ_3_3 = Control(
        control_id="PCI-3.3",
        framework=ControlFramework.PCI_DSS,
        title="Card verification code is not stored",
        description="Card verification code or value (three or four digits) is not stored after authorization.",
        category="Data Protection",
    )

    REQ_3_4 = Control(
        control_id="PCI-3.4",
        framework=ControlFramework.PCI_DSS,
        title="Primary account number (PAN) is masked when displayed",
        description="PAN is masked when displayed (the first six and last four digits are the maximum number of digits to be displayed).",
        category="Data Protection",
    )

    REQ_3_5 = Control(
        control_id="PCI-3.5",
        framework=ControlFramework.PCI_DSS,
        title="PAN is secured with cryptography when stored",
        description="PAN is secured with strong cryptography when stored, including on portable digital media, backup media, and logs.",
        category="Data Protection",
    )

    REQ_3_6 = Control(
        control_id="PCI-3.6",
        framework=ControlFramework.PCI_DSS,
        title="Cryptographic key management",
        description="Procedures are implemented for cryptographic key management for keys used to secure stored account data.",
        category="Data Protection",
    )

    REQ_3_7 = Control(
        control_id="PCI-3.7",
        framework=ControlFramework.PCI_DSS,
        title="Inventory of system components that store account data",
        description="An inventory of system components that store account data is maintained.",
        category="Data Protection",
    )

    # Requirement 4: Protect cardholder data with strong cryptography during transmission
    REQ_4_1 = Control(
        control_id="PCI-4.1",
        framework=ControlFramework.PCI_DSS,
        title="Strong cryptography for PAN transmission over open networks",
        description="Strong cryptography and security protocols are used to protect PAN during transmission over open, public networks.",
        category="Transmission Security",
    )

    REQ_4_2 = Control(
        control_id="PCI-4.2",
        framework=ControlFramework.PCI_DSS,
        title="End-user messaging technologies do not expose PAN",
        description="PAN is never sent via end-user messaging technologies (email, instant messaging, SMS, chat).",
        category="Transmission Security",
    )

    # Requirement 5: Protect all systems and networks from malicious software
    REQ_5_1 = Control(
        control_id="PCI-5.1",
        framework=ControlFramework.PCI_DSS,
        title="Anti-malware mechanisms are deployed",
        description="Anti-malware mechanisms are deployed on all systems commonly affected by malicious software.",
        category="Malware Protection",
    )

    REQ_5_2 = Control(
        control_id="PCI-5.2",
        framework=ControlFramework.PCI_DSS,
        title="Anti-malware mechanisms are kept current",
        description="Anti-malware mechanisms are kept current, perform automatic scans, and generate audit logs.",
        category="Malware Protection",
    )

    REQ_5_3 = Control(
        control_id="PCI-5.3",
        framework=ControlFramework.PCI_DSS,
        title="Anti-malware mechanisms cannot be disabled or altered",
        description="Anti-malware mechanisms cannot be disabled or altered by users, unless specifically authorized by management.",
        category="Malware Protection",
    )

    # Requirement 6: Develop and maintain secure systems and software
    REQ_6_1 = Control(
        control_id="PCI-6.1",
        framework=ControlFramework.PCI_DSS,
        title="Security patches are installed within one month",
        description="Security patches are installed within one month of release for all system components.",
        category="Secure Development",
    )

    REQ_6_2 = Control(
        control_id="PCI-6.2",
        framework=ControlFramework.PCI_DSS,
        title="Software is developed securely",
        description="Software is developed securely in accordance with industry-accepted secure coding guidelines.",
        category="Secure Development",
    )

    REQ_6_3 = Control(
        control_id="PCI-6.3",
        framework=ControlFramework.PCI_DSS,
        title="Software security vulnerabilities are identified and addressed",
        description="Software security vulnerabilities are identified and addressed through a vulnerability management process.",
        category="Secure Development",
    )

    REQ_6_4 = Control(
        control_id="PCI-6.4",
        framework=ControlFramework.PCI_DSS,
        title="Public-facing web applications are protected",
        description="Public-facing web applications are protected against attacks through automated technical solutions.",
        category="Secure Development",
    )

    # Requirement 7: Restrict access to system components and cardholder data
    REQ_7_1 = Control(
        control_id="PCI-7.1",
        framework=ControlFramework.PCI_DSS,
        title="Access is limited to system components and cardholder data",
        description="Access to system components and cardholder data is limited to only those individuals whose job requires such access.",
        category="Access Control",
    )

    REQ_7_2 = Control(
        control_id="PCI-7.2",
        framework=ControlFramework.PCI_DSS,
        title="Access is assigned based on job classification and function",
        description="Access to system components and cardholder data is assigned based on an individual's job classification and function.",
        category="Access Control",
    )

    REQ_7_3 = Control(
        control_id="PCI-7.3",
        framework=ControlFramework.PCI_DSS,
        title="Access rights are reviewed at least once every six months",
        description="Access rights are reviewed at least once every six months to confirm appropriate access.",
        category="Access Control",
    )

    # Requirement 8: Identify users and authenticate access to system components
    REQ_8_1 = Control(
        control_id="PCI-8.1",
        framework=ControlFramework.PCI_DSS,
        title="User identification policies and procedures",
        description="Policies and procedures are defined and implemented for user identification management.",
        category="Identity and Authentication",
    )

    REQ_8_2 = Control(
        control_id="PCI-8.2",
        framework=ControlFramework.PCI_DSS,
        title="User authentication is managed securely",
        description="User authentication is managed securely, including password/passphrase requirements and multi-factor authentication.",
        category="Identity and Authentication",
    )

    REQ_8_3 = Control(
        control_id="PCI-8.3",
        framework=ControlFramework.PCI_DSS,
        title="Multi-factor authentication (MFA) is implemented",
        description="MFA is implemented for all access into the cardholder data environment.",
        category="Identity and Authentication",
    )

    REQ_8_4 = Control(
        control_id="PCI-8.4",
        framework=ControlFramework.PCI_DSS,
        title="User authentication credentials are protected",
        description="User authentication credentials are protected during transmission and storage.",
        category="Identity and Authentication",
    )

    REQ_8_5 = Control(
        control_id="PCI-8.5",
        framework=ControlFramework.PCI_DSS,
        title="Service provider personnel authentication",
        description="Service provider personnel with remote access to the cardholder data environment use MFA.",
        category="Identity and Authentication",
    )

    REQ_8_6 = Control(
        control_id="PCI-8.6",
        framework=ControlFramework.PCI_DSS,
        title="Passwords/passphrases are changed periodically",
        description="Passwords/passphrases are changed periodically and not reused.",
        category="Identity and Authentication",
    )

    REQ_8_7 = Control(
        control_id="PCI-8.7",
        framework=ControlFramework.PCI_DSS,
        title="Shared and generic accounts are prohibited",
        description="Shared, generic, or group accounts, passwords, or other authentication methods are prohibited.",
        category="Identity and Authentication",
    )

    REQ_8_8 = Control(
        control_id="PCI-8.8",
        framework=ControlFramework.PCI_DSS,
        title="Account lockout mechanism",
        description="An account lockout mechanism is implemented to prevent repeated access attempts.",
        category="Identity and Authentication",
    )

    # Requirement 9: Restrict physical access to cardholder data
    REQ_9_1 = Control(
        control_id="PCI-9.1",
        framework=ControlFramework.PCI_DSS,
        title="Physical security controls are implemented",
        description="Appropriate physical security controls are implemented to restrict physical access to systems in the cardholder data environment.",
        category="Physical Security",
    )

    REQ_9_2 = Control(
        control_id="PCI-9.2",
        framework=ControlFramework.PCI_DSS,
        title="Physical access controls for sensitive areas",
        description="Physical access controls are implemented for sensitive areas within the cardholder data environment.",
        category="Physical Security",
    )

    REQ_9_3 = Control(
        control_id="PCI-9.3",
        framework=ControlFramework.PCI_DSS,
        title="Physical access to cardholder data is restricted",
        description="Physical access to cardholder data is restricted to only authorized personnel.",
        category="Physical Security",
    )

    REQ_9_4 = Control(
        control_id="PCI-9.4",
        framework=ControlFramework.PCI_DSS,
        title="Media containing cardholder data is securely stored",
        description="Media containing cardholder data is securely stored, accessed, distributed, and destroyed.",
        category="Physical Security",
    )

    # Requirement 10: Log and monitor all access to system components and cardholder data
    REQ_10_1 = Control(
        control_id="PCI-10.1",
        framework=ControlFramework.PCI_DSS,
        title="Audit logs are implemented",
        description="Audit logs are implemented to enable the detection, monitoring, and analysis of security events.",
        category="Logging and Monitoring",
    )

    REQ_10_2 = Control(
        control_id="PCI-10.2",
        framework=ControlFramework.PCI_DSS,
        title="Audit logs capture specific events",
        description="Audit logs capture specific events including all individual user access to cardholder data.",
        category="Logging and Monitoring",
    )

    REQ_10_3 = Control(
        control_id="PCI-10.3",
        framework=ControlFramework.PCI_DSS,
        title="Audit log entries include required elements",
        description="Audit log entries include required elements such as user identification, type of event, date and time, and outcome.",
        category="Logging and Monitoring",
    )

    REQ_10_4 = Control(
        control_id="PCI-10.4",
        framework=ControlFramework.PCI_DSS,
        title="Time synchronization is implemented",
        description="Time synchronization is implemented across all systems to ensure accurate time stamps in audit logs.",
        category="Logging and Monitoring",
    )

    REQ_10_5 = Control(
        control_id="PCI-10.5",
        framework=ControlFramework.PCI_DSS,
        title="Audit logs are protected from unauthorized modification",
        description="Audit logs are protected from unauthorized modification and deletion.",
        category="Logging and Monitoring",
    )

    REQ_10_6 = Control(
        control_id="PCI-10.6",
        framework=ControlFramework.PCI_DSS,
        title="Audit logs are reviewed regularly",
        description="Audit logs are reviewed regularly to identify anomalies or suspicious activity.",
        category="Logging and Monitoring",
    )

    REQ_10_7 = Control(
        control_id="PCI-10.7",
        framework=ControlFramework.PCI_DSS,
        title="Audit log history is retained",
        description="Audit log history is retained for at least one year, with a minimum of three months immediately available for analysis.",
        category="Logging and Monitoring",
    )

    # Requirement 11: Test security of systems and networks regularly
    REQ_11_1 = Control(
        control_id="PCI-11.1",
        framework=ControlFramework.PCI_DSS,
        title="Security testing is performed regularly",
        description="Security testing is performed regularly to identify and address security vulnerabilities.",
        category="Security Testing",
    )

    REQ_11_2 = Control(
        control_id="PCI-11.2",
        framework=ControlFramework.PCI_DSS,
        title="Vulnerability scans are performed",
        description="Internal and external vulnerability scans are performed at least quarterly and after significant changes.",
        category="Security Testing",
    )

    REQ_11_3 = Control(
        control_id="PCI-11.3",
        framework=ControlFramework.PCI_DSS,
        title="Penetration testing is performed",
        description="Penetration testing is performed at least annually and after significant infrastructure or application changes.",
        category="Security Testing",
    )

    REQ_11_4 = Control(
        control_id="PCI-11.4",
        framework=ControlFramework.PCI_DSS,
        title="Intrusion detection and prevention mechanisms",
        description="Intrusion detection and/or prevention mechanisms are implemented to detect and prevent intrusions.",
        category="Security Testing",
    )

    REQ_11_5 = Control(
        control_id="PCI-11.5",
        framework=ControlFramework.PCI_DSS,
        title="Change detection mechanisms",
        description="Change detection mechanisms are implemented to alert personnel to unauthorized modifications.",
        category="Security Testing",
    )

    # Requirement 12: Support security with organizational policies and programs
    REQ_12_1 = Control(
        control_id="PCI-12.1",
        framework=ControlFramework.PCI_DSS,
        title="Security policy is established and maintained",
        description="A security policy is established, published, maintained, and disseminated to all relevant personnel.",
        category="Policy and Governance",
    )

    REQ_12_2 = Control(
        control_id="PCI-12.2",
        framework=ControlFramework.PCI_DSS,
        title="Acceptable use policy",
        description="An acceptable use policy is established for the use of technology assets.",
        category="Policy and Governance",
    )

    REQ_12_3 = Control(
        control_id="PCI-12.3",
        framework=ControlFramework.PCI_DSS,
        title="Risk assessment is performed",
        description="A formal risk assessment is performed at least annually and upon significant changes.",
        category="Policy and Governance",
    )

    REQ_12_4 = Control(
        control_id="PCI-12.4",
        framework=ControlFramework.PCI_DSS,
        title="Security awareness program",
        description="A security awareness program is implemented to educate personnel about cardholder data security.",
        category="Policy and Governance",
    )

    REQ_12_5 = Control(
        control_id="PCI-12.5",
        framework=ControlFramework.PCI_DSS,
        title="Security responsibilities are assigned",
        description="Security responsibilities are assigned to specific personnel.",
        category="Policy and Governance",
    )

    REQ_12_6 = Control(
        control_id="PCI-12.6",
        framework=ControlFramework.PCI_DSS,
        title="Incident response plan",
        description="An incident response plan is established, maintained, and tested.",
        category="Policy and Governance",
    )

    REQ_12_7 = Control(
        control_id="PCI-12.7",
        framework=ControlFramework.PCI_DSS,
        title="Personnel screening",
        description="Personnel are screened prior to hire to minimize the risk of attacks from internal sources.",
        category="Policy and Governance",
    )

    REQ_12_8 = Control(
        control_id="PCI-12.8",
        framework=ControlFramework.PCI_DSS,
        title="Service provider management",
        description="Service providers are managed to maintain PCI DSS compliance.",
        category="Policy and Governance",
    )

    REQ_12_9 = Control(
        control_id="PCI-12.9",
        framework=ControlFramework.PCI_DSS,
        title="Service provider compliance evidence",
        description="Evidence of PCI DSS compliance is maintained for service providers.",
        category="Policy and Governance",
    )

    REQ_12_10 = Control(
        control_id="PCI-12.10",
        framework=ControlFramework.PCI_DSS,
        title="Targeted risk analysis",
        description="A targeted risk analysis is performed for each PCI DSS requirement that is met with a customized approach.",
        category="Policy and Governance",
    )

    REQ_12_11 = Control(
        control_id="PCI-12.11",
        framework=ControlFramework.PCI_DSS,
        title="PCI DSS compliance is reviewed",
        description="PCI DSS compliance is reviewed at least annually.",
        category="Policy and Governance",
    )

    @classmethod
    def all_controls(cls) -> list[Control]:
        """Return all PCI DSS controls."""
        return [
            cls.REQ_1_1, cls.REQ_1_2, cls.REQ_1_3, cls.REQ_1_4,
            cls.REQ_2_1, cls.REQ_2_2, cls.REQ_2_3,
            cls.REQ_3_1, cls.REQ_3_2, cls.REQ_3_3, cls.REQ_3_4, cls.REQ_3_5, cls.REQ_3_6, cls.REQ_3_7,
            cls.REQ_4_1, cls.REQ_4_2,
            cls.REQ_5_1, cls.REQ_5_2, cls.REQ_5_3,
            cls.REQ_6_1, cls.REQ_6_2, cls.REQ_6_3, cls.REQ_6_4,
            cls.REQ_7_1, cls.REQ_7_2, cls.REQ_7_3,
            cls.REQ_8_1, cls.REQ_8_2, cls.REQ_8_3, cls.REQ_8_4, cls.REQ_8_5, cls.REQ_8_6, cls.REQ_8_7, cls.REQ_8_8,
            cls.REQ_9_1, cls.REQ_9_2, cls.REQ_9_3, cls.REQ_9_4,
            cls.REQ_10_1, cls.REQ_10_2, cls.REQ_10_3, cls.REQ_10_4, cls.REQ_10_5, cls.REQ_10_6, cls.REQ_10_7,
            cls.REQ_11_1, cls.REQ_11_2, cls.REQ_11_3, cls.REQ_11_4, cls.REQ_11_5,
            cls.REQ_12_1, cls.REQ_12_2, cls.REQ_12_3, cls.REQ_12_4, cls.REQ_12_5,
            cls.REQ_12_6, cls.REQ_12_7, cls.REQ_12_8, cls.REQ_12_9, cls.REQ_12_10, cls.REQ_12_11,
        ]


class PCIDSSRequirement:
    """PCI DSS v4.0 requirement assessment."""

    def __init__(self, controls: list[Control] | None = None) -> None:
        self.controls = controls or PCIDSSControl.all_controls()

    def assess(self) -> dict[str, object]:
        """Run assessment and return summary."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        na = sum(1 for c in self.controls if c.status == ControlStatus.NOT_APPLICABLE)
        return {
            "framework": "PCI_DSS",
            "totalControls": total,
            "implemented": implemented,
            "partiallyImplemented": partial,
            "notImplemented": not_impl,
            "notApplicable": na,
            "complianceRate": round((implemented / total) * 100, 1) if total else 0.0,
        }
