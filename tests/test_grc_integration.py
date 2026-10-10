"""Tests for the GRC integration kernel.

Covers evidence collection, control definitions, cross-framework mapping,
and compliance assessment for ISO 42001, SOC 2, PCI DSS, DORA, SEC 8-K,
and FFIEC CAT.
"""
import unittest

from kernels.grc_integration import (
    Control,
    ControlFramework,
    ControlMapping,
    ControlRegistry,
    ControlStatus,
    DORAControl,
    DORARegulation,
    Evidence,
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    EvidenceStore,
    FFIECCATControl,
    FFIEC_CAT_Domain,
    ISO42001Assessment,
    ISO42001Control,
    PCIDSSControl,
    PCIDSSRequirement,
    SEC8KControl,
    SEC8KFiling,
    SOC2Control,
    SOC2TrustServiceCriteria,
)
from kernels.grc_integration.mappings import build_default_mappings


class EvidenceTests(unittest.TestCase):
    def test_evidence_creation_and_verification(self):
        store = EvidenceStore()
        evidence = store.create(
            control_id="ISO42001-6.1",
            framework="ISO42001",
            description="Risk assessment completed for Q3 2026",
            collector_id="auditor-1",
            data={"scope": "AI system lifecycle", "findings": 3},
        )
        self.assertTrue(evidence.verify())
        self.assertEqual(evidence.control_id, "ISO42001-6.1")
        self.assertEqual(evidence.framework, "ISO42001")
        self.assertEqual(len(store), 1)

    def test_evidence_integrity_failure(self):
        store = EvidenceStore()
        evidence = store.create(
            control_id="SOC2-SC6.1",
            framework="SOC2",
            description="Access control review",
            collector_id="auditor-2",
            data={"users_reviewed": 42},
        )
        # Tamper with the evidence data
        evidence.data["users_reviewed"] = 99
        self.assertFalse(evidence.verify())

    def test_evidence_not_found(self):
        store = EvidenceStore()
        with self.assertRaises(EvidenceNotFoundError):
            store.get("nonexistent-id")

    def test_list_by_control(self):
        store = EvidenceStore()
        store.create(
            control_id="PCI-3.5",
            framework="PCI_DSS",
            description="PAN encryption verification",
            collector_id="auditor-3",
            data={"encrypted": True},
        )
        store.create(
            control_id="PCI-3.5",
            framework="PCI_DSS",
            description="Key rotation check",
            collector_id="auditor-3",
            data={"rotated": True},
        )
        store.create(
            control_id="PCI-10.1",
            framework="PCI_DSS",
            description="Audit log review",
            collector_id="auditor-4",
            data={"logs_present": True},
        )
        results = store.list_by_control("PCI-3.5")
        self.assertEqual(len(results), 2)

    def test_list_by_framework(self):
        store = EvidenceStore()
        store.create(
            control_id="DORA-3.1",
            framework="DORA",
            description="Incident response test",
            collector_id="auditor-5",
            data={"tested": True},
        )
        store.create(
            control_id="DORA-4.1",
            framework="DORA",
            description="Resilience testing program",
            collector_id="auditor-5",
            data={"program_active": True},
        )
        store.create(
            control_id="8K-1.05",
            framework="SEC_8K",
            description="Cybersecurity incident disclosure",
            collector_id="auditor-6",
            data={"disclosed": True},
        )
        results = store.list_by_framework("DORA")
        self.assertEqual(len(results), 2)

    def test_verify_all(self):
        store = EvidenceStore()
        store.create(
            control_id="FFIEC-1.1",
            framework="FFIEC_CAT",
            description="Governance review",
            collector_id="auditor-7",
            data={"board_oversight": True},
        )
        store.create(
            control_id="FFIEC-3.1",
            framework="FFIEC_CAT",
            description="Preventive controls assessment",
            collector_id="auditor-7",
            data={"controls_active": True},
        )
        results = store.verify_all()
        self.assertEqual(len(results), 2)
        self.assertTrue(all(results.values()))

    def test_evidence_to_dict_roundtrip(self):
        store = EvidenceStore()
        evidence = store.create(
            control_id="ISO42001-5.1",
            framework="ISO42001",
            description="Leadership commitment evidence",
            collector_id="auditor-8",
            data={"policy_approved": True},
        )
        d = evidence.to_dict()
        restored = Evidence.from_dict(d)
        self.assertEqual(restored.control_id, evidence.control_id)
        self.assertEqual(restored.framework, evidence.framework)
        self.assertEqual(restored.sha256, evidence.sha256)
        self.assertTrue(restored.verify())


class ControlRegistryTests(unittest.TestCase):
    def test_register_and_retrieve(self):
        registry = ControlRegistry()
        control = Control(
            control_id="TEST-1.0",
            framework=ControlFramework.ISO_42001,
            title="Test Control",
            description="A test control",
            category="Test",
        )
        registry.register(control)
        retrieved = registry.get("TEST-1.0")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Control")

    def test_list_by_framework(self):
        registry = ControlRegistry()
        for ctrl in ISO42001Control.all_controls():
            registry.register(ctrl)
        for ctrl in SOC2Control.all_controls():
            registry.register(ctrl)
        iso_controls = registry.list_by_framework(ControlFramework.ISO_42001)
        soc2_controls = registry.list_by_framework(ControlFramework.SOC2)
        self.assertEqual(len(iso_controls), 22)
        self.assertEqual(len(soc2_controls), 32)

    def test_coverage_summary(self):
        registry = ControlRegistry()
        for ctrl in ISO42001Control.all_controls():
            registry.register(ctrl)
        summary = registry.coverage_summary()
        self.assertIn("ISO42001", summary)
        self.assertEqual(summary["ISO42001"]["total"], 22)
        self.assertEqual(summary["ISO42001"]["notImplemented"], 22)

    def test_control_to_dict_roundtrip(self):
        control = Control(
            control_id="TEST-2.0",
            framework=ControlFramework.PCI_DSS,
            title="Test PCI Control",
            description="A test PCI control",
            category="Test",
            status=ControlStatus.IMPLEMENTED,
            evidence_ids=["ev-1", "ev-2"],
        )
        d = control.to_dict()
        restored = Control.from_dict(d)
        self.assertEqual(restored.control_id, control.control_id)
        self.assertEqual(restored.framework, control.framework)
        self.assertEqual(restored.status, control.status)
        self.assertEqual(restored.evidence_ids, control.evidence_ids)


class CrossFrameworkMappingTests(unittest.TestCase):
    def test_default_mappings_exist(self):
        mappings = build_default_mappings()
        self.assertGreater(len(mappings), 0)

    def test_mapping_to_dict(self):
        mappings = build_default_mappings()
        for m in mappings:
            d = m.to_dict()
            self.assertIn("sourceControlId", d)
            self.assertIn("sourceFramework", d)
            self.assertIn("mappings", d)
            self.assertIsInstance(d["mappings"], list)

    def test_mapping_references_valid_frameworks(self):
        mappings = build_default_mappings()
        valid_frameworks = {fw.value for fw in ControlFramework}
        for m in mappings:
            self.assertIn(m.source_framework.value, valid_frameworks)
            for fw, cid in m.mappings:
                self.assertIn(fw.value, valid_frameworks)


class ISO42001Tests(unittest.TestCase):
    def test_all_controls_present(self):
        controls = ISO42001Control.all_controls()
        self.assertEqual(len(controls), 22)

    def test_assessment_structure(self):
        assessment = ISO42001Assessment()
        result = assessment.assess()
        self.assertEqual(result["framework"], "ISO42001")
        self.assertEqual(result["totalControls"], 22)
        self.assertIn("complianceRate", result)

    def test_control_categories(self):
        controls = ISO42001Control.all_controls()
        categories = {c.category for c in controls}
        self.assertIn("Context", categories)
        self.assertIn("Leadership", categories)
        self.assertIn("Planning", categories)
        self.assertIn("Support", categories)
        self.assertIn("Operation", categories)
        self.assertIn("Performance", categories)
        self.assertIn("Improvement", categories)


class SOC2Tests(unittest.TestCase):
    def test_all_controls_present(self):
        controls = SOC2Control.all_controls()
        self.assertEqual(len(controls), 32)

    def test_assessment_structure(self):
        assessment = SOC2TrustServiceCriteria()
        result = assessment.assess()
        self.assertEqual(result["framework"], "SOC2")
        self.assertEqual(result["totalControls"], 32)
        self.assertIn("complianceRate", result)

    def test_control_categories(self):
        controls = SOC2Control.all_controls()
        categories = {c.category for c in controls}
        self.assertIn("Common Criteria", categories)
        self.assertIn("Security", categories)
        self.assertIn("Availability", categories)
        self.assertIn("Processing Integrity", categories)
        self.assertIn("Confidentiality", categories)
        self.assertIn("Privacy", categories)


class PCIDSSTests(unittest.TestCase):
    def test_all_controls_present(self):
        controls = PCIDSSControl.all_controls()
        self.assertEqual(len(controls), 61)

    def test_assessment_structure(self):
        assessment = PCIDSSRequirement()
        result = assessment.assess()
        self.assertEqual(result["framework"], "PCI_DSS")
        self.assertEqual(result["totalControls"], 61)
        self.assertIn("complianceRate", result)

    def test_control_categories(self):
        controls = PCIDSSControl.all_controls()
        categories = {c.category for c in controls}
        self.assertIn("Network Security", categories)
        self.assertIn("Data Protection", categories)
        self.assertIn("Access Control", categories)
        self.assertIn("Logging and Monitoring", categories)
        self.assertIn("Policy and Governance", categories)


class DORATests(unittest.TestCase):
    def test_all_controls_present(self):
        controls = DORAControl.all_controls()
        self.assertEqual(len(controls), 23)

    def test_assessment_structure(self):
        assessment = DORARegulation()
        result = assessment.assess()
        self.assertEqual(result["framework"], "DORA")
        self.assertEqual(result["totalControls"], 23)
        self.assertIn("complianceRate", result)

    def test_control_categories(self):
        controls = DORAControl.all_controls()
        categories = {c.category for c in controls}
        self.assertIn("Governance", categories)
        self.assertIn("ICT Risk Management", categories)
        self.assertIn("Incident Management", categories)
        self.assertIn("Resilience Testing", categories)
        self.assertIn("Third-Party Risk", categories)


class SEC8KTests(unittest.TestCase):
    def test_all_controls_present(self):
        controls = SEC8KControl.all_controls()
        self.assertEqual(len(controls), 29)

    def test_assessment_structure(self):
        assessment = SEC8KFiling()
        result = assessment.assess()
        self.assertEqual(result["framework"], "SEC_8K")
        self.assertEqual(result["totalControls"], 29)
        self.assertIn("complianceRate", result)

    def test_cybersecurity_controls_present(self):
        controls = SEC8KControl.all_controls()
        cyber_controls = [c for c in controls if c.category == "Cybersecurity"]
        self.assertEqual(len(cyber_controls), 2)


class FFIECCATTests(unittest.TestCase):
    def test_all_controls_present(self):
        controls = FFIECCATControl.all_controls()
        self.assertEqual(len(controls), 24)

    def test_assessment_structure(self):
        assessment = FFIEC_CAT_Domain()
        result = assessment.assess()
        self.assertEqual(result["framework"], "FFIEC_CAT")
        self.assertEqual(result["totalControls"], 24)
        self.assertIn("complianceRate", result)

    def test_control_categories(self):
        controls = FFIECCATControl.all_controls()
        categories = {c.category for c in controls}
        self.assertIn("Cyber Risk Management and Oversight", categories)
        self.assertIn("Threat Intelligence and Collaboration", categories)
        self.assertIn("Cybersecurity Controls", categories)
        self.assertIn("External Dependency Management", categories)
        self.assertIn("Cyber Incident Management and Resilience", categories)


class IntegrationTests(unittest.TestCase):
    def test_full_registry_with_all_frameworks(self):
        registry = ControlRegistry()
        for ctrl in ISO42001Control.all_controls():
            registry.register(ctrl)
        for ctrl in SOC2Control.all_controls():
            registry.register(ctrl)
        for ctrl in PCIDSSControl.all_controls():
            registry.register(ctrl)
        for ctrl in DORAControl.all_controls():
            registry.register(ctrl)
        for ctrl in SEC8KControl.all_controls():
            registry.register(ctrl)
        for ctrl in FFIECCATControl.all_controls():
            registry.register(ctrl)

        self.assertEqual(len(registry), 22 + 32 + 61 + 23 + 29 + 24)

        summary = registry.coverage_summary()
        self.assertEqual(len(summary), 6)
        for fw_name, stats in summary.items():
            self.assertIn("total", stats)
            self.assertIn("implemented", stats)
            self.assertIn("notImplemented", stats)

    def test_evidence_lifecycle_with_registry(self):
        registry = ControlRegistry()
        evidence_store = EvidenceStore()

        # Register a control
        control = Control(
            control_id="TEST-EVIDENCE-1",
            framework=ControlFramework.ISO_42001,
            title="Evidence Test Control",
            description="Control for evidence lifecycle test",
            category="Test",
        )
        registry.register(control)

        # Create evidence
        evidence = evidence_store.create(
            control_id="TEST-EVIDENCE-1",
            framework="ISO42001",
            description="Test evidence",
            collector_id="test-auditor",
            data={"test": True},
        )

        # Link evidence to control
        control.evidence_ids.append(evidence.evidence_id)

        # Verify linkage
        self.assertEqual(len(control.evidence_ids), 1)
        retrieved = evidence_store.get(evidence.evidence_id)
        self.assertEqual(retrieved.control_id, "TEST-EVIDENCE-1")

    def test_cross_framework_mapping_with_registry(self):
        registry = ControlRegistry()
        for ctrl in ISO42001Control.all_controls():
            registry.register(ctrl)
        for ctrl in SOC2Control.all_controls():
            registry.register(ctrl)
        for ctrl in PCIDSSControl.all_controls():
            registry.register(ctrl)
        for ctrl in DORAControl.all_controls():
            registry.register(ctrl)
        for ctrl in SEC8KControl.all_controls():
            registry.register(ctrl)
        for ctrl in FFIECCATControl.all_controls():
            registry.register(ctrl)

        # Add mappings
        for mapping in build_default_mappings():
            registry.add_mapping(mapping)

        # Verify mappings are retrievable
        mappings = registry.get_mappings("SOC2-SC6.1")
        self.assertGreater(len(mappings), 0)
        # Should map to PCI DSS and FFIEC CAT
        target_frameworks = {fw for fw, _ in mappings}
        self.assertIn(ControlFramework.PCI_DSS, target_frameworks)
        self.assertIn(ControlFramework.FFIEC_CAT, target_frameworks)


if __name__ == "__main__":
    unittest.main()
