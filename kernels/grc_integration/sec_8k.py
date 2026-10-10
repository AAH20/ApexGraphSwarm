"""SEC 8-K filing controls.

Defines controls for SEC Form 8-K material event reporting requirements,
covering disclosure obligations, timing, and cybersecurity incidents.
"""
from __future__ import annotations

from .controls import Control, ControlFramework, ControlStatus


class SEC8KControl:
    """SEC 8-K filing control definitions."""

    # Item 1.01: Entry into a Material Definitive Agreement
    ITEM_1_01 = Control(
        control_id="8K-1.01",
        framework=ControlFramework.SEC_8K,
        title="Entry into a Material Definitive Agreement",
        description="Disclose entry into material definitive agreements not made in the ordinary course of business.",
        category="Material Agreements",
    )

    # Item 1.02: Termination of a Material Definitive Agreement
    ITEM_1_02 = Control(
        control_id="8K-1.02",
        framework=ControlFramework.SEC_8K,
        title="Termination of a Material Definitive Agreement",
        description="Disclose termination of material definitive agreements not made in the ordinary course of business.",
        category="Material Agreements",
    )

    # Item 1.03: Bankruptcy or Receivership
    ITEM_1_03 = Control(
        control_id="8K-1.03",
        framework=ControlFramework.SEC_8K,
        title="Bankruptcy or Receivership",
        description="Disclose bankruptcy or receivership of the registrant or its significant subsidiaries.",
        category="Financial Distress",
    )

    # Item 1.04: Mine Safety Reporting
    ITEM_1_04 = Control(
        control_id="8K-1.04",
        framework=ControlFramework.SEC_8K,
        title="Mine Safety - Reporting of Shutdowns and Patterns of Violations",
        description="Disclose mine safety reporting for mine operations.",
        category="Industry-Specific",
    )

    # Item 2.01: Completion of Acquisition or Disposition of Assets
    ITEM_2_01 = Control(
        control_id="8K-2.01",
        framework=ControlFramework.SEC_8K,
        title="Completion of Acquisition or Disposition of Assets",
        description="Disclose completion of acquisition or disposition of a significant amount of assets.",
        category="Acquisitions and Dispositions",
    )

    # Item 2.02: Results of Operations and Financial Condition
    ITEM_2_02 = Control(
        control_id="8K-2.02",
        framework=ControlFramework.SEC_8K,
        title="Results of Operations and Financial Condition",
        description="Disclose material non-public information regarding results of operations or financial condition for a completed period.",
        category="Financial Results",
    )

    # Item 2.03: Creation of a Direct Financial Obligation
    ITEM_2_03 = Control(
        control_id="8K-2.03",
        framework=ControlFramework.SEC_8K,
        title="Creation of a Direct Financial Obligation",
        description="Disclosure of creation of a direct financial obligation or an obligation under an off-balance sheet arrangement.",
        category="Financial Obligations",
    )

    # Item 2.04: Triggering Events That Accelerate or Increase a Direct Financial Obligation
    ITEM_2_04 = Control(
        control_id="8K-2.04",
        framework=ControlFramework.SEC_8K,
        title="Triggering Events That Accelerate or Increase a Direct Financial Obligation",
        description="Disclose triggering events that accelerate or increase a direct financial obligation.",
        category="Financial Obligations",
    )

    # Item 2.05: Costs Associated with Exit or Disposal Activities
    ITEM_2_05 = Control(
        control_id="8K-2.05",
        framework=ControlFramework.SEC_8K,
        title="Costs Associated with Exit or Disposal Activities",
        description="Disclosure of material costs associated with exit or disposal activities.",
        category="Restructuring",
    )

    # Item 2.06: Material Impairments
    ITEM_2_06 = Control(
        control_id="8K-2.06",
        framework=ControlFramework.SEC_8K,
        title="Material Impairments",
        description="Disclose material impairments of assets, including goodwill.",
        category="Restructuring",
    )

    # Item 3.01: Notice of Delisting
    ITEM_3_01 = Control(
        control_id="8K-3.01",
        framework=ControlFramework.SEC_8K,
        title="Notice of Delisting or Failure to Satisfy a Continued Listing Rule",
        description="Disclosure of receipt of notice of delisting or failure to satisfy continued listing rule or standard.",
        category="Listing Status",
    )

    # Item 3.02: Unregistered Sales of Equity Securities
    ITEM_3_02 = Control(
        control_id="8K-3.02",
        framework=ControlFramework.SEC_8K,
        title="Unregistered Sales of Equity Securities",
        description="Disclosure of unregistered sales of equity securities in amounts that are material.",
        category="Securities Offerings",
    )

    # Item 3.03: Material Modification to Rights of Security Holders
    ITEM_3_03 = Control(
        control_id="8K-3.03",
        framework=ControlFramework.SEC_8K,
        title="Material Modification to Rights of Security Holders",
        description="Disclosure of material modification to rights of security holders.",
        category="Corporate Governance",
    )

    # Item 4.01: Changes in Registrant's Certifying Accountant
    ITEM_4_01 = Control(
        control_id="8K-4.01",
        framework=ControlFramework.SEC_8K,
        title="Changes in Registrant's Certifying Accountant",
        description="Disclosure of changes in the registrant's certifying accountant.",
        category="Auditor Changes",
    )

    # Item 4.02: Non-Reliance on Previously Issued Financial Statements
    ITEM_4_02 = Control(
        control_id="8K-4.02",
        framework=ControlFramework.SEC_8K,
        title="Non-Reliance on Previously Issued Financial Statements or a Related Audit Report",
        description="Disclosure of determination that previously issued financial statements should not be relied upon.",
        category="Financial Restatement",
    )

    # Item 5.01: Changes in Control of Registrant
    ITEM_5_01 = Control(
        control_id="8K-5.01",
        framework=ControlFramework.SEC_8K,
        title="Changes in Control of Registrant",
        description="Disclosure of change in control of the registrant.",
        category="Corporate Governance",
    )

    # Item 5.02: Departure of Directors or Certain Officers
    ITEM_5_02 = Control(
        control_id="8K-5.02",
        framework=ControlFramework.SEC_8K,
        title="Departure of Directors or Certain Officers; Election of Directors",
        description="Disclosure of departure, election, or appointment of directors or principal officers.",
        category="Corporate Governance",
    )

    # Item 5.03: Amendments to Articles of Incorporation or Bylaws
    ITEM_5_03 = Control(
        control_id="8K-5.03",
        framework=ControlFramework.SEC_8K,
        title="Amendments to Articles of Incorporation or Bylaws",
        description="Disclosure of amendments to articles of incorporation or bylaws.",
        category="Corporate Governance",
    )

    # Item 5.04: Temporary Suspension of Trading Under Registrant's Employee Benefit Plans
    ITEM_5_04 = Control(
        control_id="8K-5.04",
        framework=ControlFramework.SEC_8K,
        title="Temporary Suspension of Trading Under Registrant's Employee Benefit Plans",
        description="Disclosure of temporary suspension of trading under employee benefit plans.",
        category="Benefit Plans",
    )

    # Item 5.05: Amendment to Registrant's Code of Ethics
    ITEM_5_05 = Control(
        control_id="8K-5.05",
        framework=ControlFramework.SEC_8K,
        title="Amendment to Registrant's Code of Ethics",
        description="Disclosure of amendment to, or waiver from, the registrant's code of ethics.",
        category="Ethics",
    )

    # Item 5.06: Change in Shell Company Status
    ITEM_5_06 = Control(
        control_id="8K-5.06",
        framework=ControlFramework.SEC_8K,
        title="Change in Shell Company Status",
        description="Disclosure of change in shell company status.",
        category="Corporate Status",
    )

    # Item 5.07: Submission of Matters to a Vote of Security Holders
    ITEM_5_07 = Control(
        control_id="8K-5.07",
        framework=ControlFramework.SEC_8K,
        title="Submission of Matters to a Vote of Security Holders",
        description="Disclosure of submission of matters to a vote of security holders.",
        category="Corporate Governance",
    )

    # Item 5.08: Shareholder Director Nominations
    ITEM_5_08 = Control(
        control_id="8K-5.08",
        framework=ControlFramework.SEC_8K,
        title="Shareholder Director Nominations",
        description="Disclosure of shareholder director nomination procedures.",
        category="Corporate Governance",
    )

    # Item 7.01: Regulation FD Disclosure
    ITEM_7_01 = Control(
        control_id="8K-7.01",
        framework=ControlFramework.SEC_8K,
        title="Regulation FD Disclosure",
        description="Disclosure of material non-public information under Regulation FD.",
        category="Regulation FD",
    )

    # Item 8.01: Other Events
    ITEM_8_01 = Control(
        control_id="8K-8.01",
        framework=ControlFramework.SEC_8K,
        title="Other Events",
        description="Disclosure of events that are not specifically called for by Form 8-K but are of material importance.",
        category="Other Disclosures",
    )

    # Item 9.01: Financial Statements and Exhibits
    ITEM_9_01 = Control(
        control_id="8K-9.01",
        framework=ControlFramework.SEC_8K,
        title="Financial Statements and Exhibits",
        description="Filing of financial statements and exhibits as required.",
        category="Exhibits",
    )

    # Cybersecurity Disclosure (Item 1.05)
    CYBERSECURITY_INCIDENT = Control(
        control_id="8K-1.05",
        framework=ControlFramework.SEC_8K,
        title="Material Cybersecurity Incidents",
        description="Disclosure of material cybersecurity incidents within four business days of determination of materiality.",
        category="Cybersecurity",
    )

    CYBERSECURITY_GOVERNANCE = Control(
        control_id="8K-1.06",
        framework=ControlFramework.SEC_8K,
        title="Cybersecurity Risk Management and Strategy Disclosure",
        description="Annual disclosure of cybersecurity risk management, strategy, and governance in Form 10-K.",
        category="Cybersecurity",
    )

    # Filing Timeliness
    FILING_TIMELINESS = Control(
        control_id="8K-TIMING",
        framework=ControlFramework.SEC_8K,
        title="Timely Filing Within Four Business Days",
        description="Reportable events must be disclosed on Form 8-K within four business days of the occurrence of the event.",
        category="Timeliness",
    )

    @classmethod
    def all_controls(cls) -> list[Control]:
        """Return all SEC 8-K controls."""
        return [
            cls.ITEM_1_01, cls.ITEM_1_02, cls.ITEM_1_03, cls.ITEM_1_04,
            cls.ITEM_2_01, cls.ITEM_2_02, cls.ITEM_2_03, cls.ITEM_2_04,
            cls.ITEM_2_05, cls.ITEM_2_06,
            cls.ITEM_3_01, cls.ITEM_3_02, cls.ITEM_3_03,
            cls.ITEM_4_01, cls.ITEM_4_02,
            cls.ITEM_5_01, cls.ITEM_5_02, cls.ITEM_5_03, cls.ITEM_5_04,
            cls.ITEM_5_05, cls.ITEM_5_06, cls.ITEM_5_07, cls.ITEM_5_08,
            cls.ITEM_7_01,
            cls.ITEM_8_01,
            cls.ITEM_9_01,
            cls.CYBERSECURITY_INCIDENT, cls.CYBERSECURITY_GOVERNANCE,
            cls.FILING_TIMELINESS,
        ]


class SEC8KFiling:
    """SEC 8-K filing compliance assessment."""

    def __init__(self, controls: list[Control] | None = None) -> None:
        self.controls = controls or SEC8KControl.all_controls()

    def assess(self) -> dict[str, object]:
        """Run assessment and return summary."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        na = sum(1 for c in self.controls if c.status == ControlStatus.NOT_APPLICABLE)
        return {
            "framework": "SEC_8K",
            "totalControls": total,
            "implemented": implemented,
            "partiallyImplemented": partial,
            "notImplemented": not_impl,
            "notApplicable": na,
            "complianceRate": round((implemented / total) * 100, 1) if total else 0.0,
        }
