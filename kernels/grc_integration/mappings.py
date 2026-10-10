"""Cross-framework control mapping for GRC compliance.

Maps equivalent controls across ISO 42001, SOC 2, PCI DSS, DORA, SEC 8-K,
and FFIEC CAT to enable unified compliance reporting.
"""
from __future__ import annotations

from .controls import ControlFramework, ControlMapping


def build_default_mappings() -> list[ControlMapping]:
    """Build the default cross-framework control mappings.

    Returns a list of ControlMapping objects that map equivalent controls
    across different compliance frameworks.
    """
    mappings: list[ControlMapping] = []

    # Access Control mappings
    mappings.append(ControlMapping(
        source_control_id="SOC2-SC6.1",
        source_framework=ControlFramework.SOC2,
        mappings=[
            (ControlFramework.PCI_DSS, "PCI-7.1"),
            (ControlFramework.PCI_DSS, "PCI-8.1"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.3"),
            (ControlFramework.ISO_42001, "ISO42001-7.1"),
        ],
    ))

    # Risk Assessment mappings
    mappings.append(ControlMapping(
        source_control_id="ISO42001-6.1",
        source_framework=ControlFramework.ISO_42001,
        mappings=[
            (ControlFramework.SOC2, "SOC2-CC3.1"),
            (ControlFramework.PCI_DSS, "PCI-12.3"),
            (ControlFramework.DORA, "DORA-2.2"),
            (ControlFramework.FFIEC_CAT, "FFIEC-1.2"),
        ],
    ))

    # Incident Management mappings
    mappings.append(ControlMapping(
        source_control_id="DORA-3.1",
        source_framework=ControlFramework.DORA,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC9.1"),
            (ControlFramework.PCI_DSS, "PCI-12.6"),
            (ControlFramework.SEC_8K, "8K-1.05"),
            (ControlFramework.FFIEC_CAT, "FFIEC-5.1"),
        ],
    ))

    # Data Protection mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-3.5",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC7.5"),
            (ControlFramework.SOC2, "SOC2-CO1.2"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.5"),
            (ControlFramework.ISO_42001, "ISO42001-8.2"),
        ],
    ))

    # Third-Party Risk mappings
    mappings.append(ControlMapping(
        source_control_id="DORA-5.1",
        source_framework=ControlFramework.DORA,
        mappings=[
            (ControlFramework.PCI_DSS, "PCI-12.8"),
            (ControlFramework.FFIEC_CAT, "FFIEC-4.1"),
            (ControlFramework.SOC2, "SOC2-CC5.1"),
        ],
    ))

    # Logging and Monitoring mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-10.1",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC7.3"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.2"),
            (ControlFramework.ISO_42001, "ISO42001-9.1"),
        ],
    ))

    # Governance mappings
    mappings.append(ControlMapping(
        source_control_id="ISO42001-5.1",
        source_framework=ControlFramework.ISO_42001,
        mappings=[
            (ControlFramework.SOC2, "SOC2-CC1.1"),
            (ControlFramework.FFIEC_CAT, "FFIEC-1.1"),
            (ControlFramework.DORA, "DORA-1.1"),
        ],
    ))

    # Business Continuity mappings
    mappings.append(ControlMapping(
        source_control_id="FFIEC-5.4",
        source_framework=ControlFramework.FFIEC_CAT,
        mappings=[
            (ControlFramework.SOC2, "SOC2-AC1.1"),
            (ControlFramework.DORA, "DORA-2.5"),
            (ControlFramework.PCI_DSS, "PCI-12.6"),
        ],
    ))

    # Secure Development mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-6.2",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC8.1"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.6"),
            (ControlFramework.ISO_42001, "ISO42001-8.1"),
        ],
    ))

    # Authentication mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-8.3",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC6.2"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.3"),
        ],
    ))

    # Network Security mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-1.1",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC7.3"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.4"),
        ],
    ))

    # Change Management mappings
    mappings.append(ControlMapping(
        source_control_id="SOC2-SC8.1",
        source_framework=ControlFramework.SOC2,
        mappings=[
            (ControlFramework.PCI_DSS, "PCI-6.1"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.6"),
        ],
    ))

    # Vulnerability Management mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-11.2",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-SC7.2"),
            (ControlFramework.FFIEC_CAT, "FFIEC-3.1"),
            (ControlFramework.DORA, "DORA-4.2"),
        ],
    ))

    # Policy mappings
    mappings.append(ControlMapping(
        source_control_id="PCI-12.1",
        source_framework=ControlFramework.PCI_DSS,
        mappings=[
            (ControlFramework.SOC2, "SOC2-CC1.1"),
            (ControlFramework.FFIEC_CAT, "FFIEC-1.5"),
            (ControlFramework.ISO_42001, "ISO42001-5.2"),
        ],
    ))

    return mappings
