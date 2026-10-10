"""Tests for the 11-tactic adversary emulation threat matrix."""
import json
import unittest

from kernels.threat_matrix import (
    AdversaryEmulator,
    DetectionRule,
    EmulationReport,
    EmulationResult,
    EmulationStatus,
    Mitigation,
    Severity,
    TacticDomain,
    Technique,
    ThreatMatrix,
    build_default_matrix,
)
from kernels.threat_matrix.detection import build_detection_rules, build_mitigations
from kernels.threat_matrix.emulator import _domain_for_technique
from kernels.threat_matrix.matrix import build_default_matrix as build_matrix


class TestTacticDomain(unittest.TestCase):
    """Test the 11 tactic domain enum."""

    def test_all_11_domains_present(self):
        expected = {
            "reconnaissance", "semantic_ingress", "context_contamination",
            "tool_discipline", "sandbox_escape", "privilege_escalation",
            "swarm_contagion", "telemetry_suppression", "financial_rail",
            "state_exfiltration", "resource_exhaustion",
        }
        actual = {d.value for d in TacticDomain}
        self.assertEqual(actual, expected)

    def test_domain_count(self):
        self.assertEqual(len(TacticDomain), 11)


class TestSeverity(unittest.TestCase):
    """Test severity levels."""

    def test_severity_levels(self):
        self.assertEqual(Severity.CRITICAL.value, "critical")
        self.assertEqual(Severity.HIGH.value, "high")
        self.assertEqual(Severity.MEDIUM.value, "medium")
        self.assertEqual(Severity.LOW.value, "low")
        self.assertEqual(Severity.INFO.value, "info")


class TestTechnique(unittest.TestCase):
    """Test Technique dataclass."""

    def test_technique_creation(self):
        t = Technique(
            id="TEST-001",
            name="Test Technique",
            description="A test technique.",
            severity=Severity.HIGH,
            kill_chain_phase="execution",
        )
        self.assertEqual(t.id, "TEST-001")
        self.assertEqual(t.name, "Test Technique")
        self.assertEqual(t.severity, Severity.HIGH)
        self.assertEqual(t.prerequisites, ())
        self.assertEqual(t.indicators, ())

    def test_technique_with_prerequisites(self):
        t = Technique(
            id="TEST-002",
            name="Dependent Technique",
            description="Depends on TEST-001.",
            severity=Severity.CRITICAL,
            kill_chain_phase="execution",
            prerequisites=("TEST-001",),
        )
        self.assertEqual(t.prerequisites, ("TEST-001",))


class TestThreatMatrix(unittest.TestCase):
    """Test ThreatMatrix container."""

    def test_empty_matrix(self):
        m = ThreatMatrix()
        self.assertEqual(m.all_techniques(), [])
        self.assertEqual(m.critical_count(), 0)

    def test_add_technique(self):
        m = ThreatMatrix()
        t = Technique(
            id="TEST-001", name="Test", description="Test",
            severity=Severity.HIGH, kill_chain_phase="execution",
        )
        m.add_technique(TacticDomain.RECONNAISSANCE, t)
        self.assertEqual(len(m.techniques_for(TacticDomain.RECONNAISSANCE)), 1)
        self.assertEqual(m.all_techniques()[0].id, "TEST-001")

    def test_critical_count(self):
        m = ThreatMatrix()
        m.add_technique(TacticDomain.RECONNAISSANCE, Technique(
            id="T-001", name="Critical", description="Test",
            severity=Severity.CRITICAL, kill_chain_phase="execution",
        ))
        m.add_technique(TacticDomain.RECONNAISSANCE, Technique(
            id="T-002", name="High", description="Test",
            severity=Severity.HIGH, kill_chain_phase="execution",
        ))
        self.assertEqual(m.critical_count(), 1)

    def test_by_severity(self):
        m = ThreatMatrix()
        m.add_technique(TacticDomain.RECONNAISSANCE, Technique(
            id="T-001", name="Critical", description="Test",
            severity=Severity.CRITICAL, kill_chain_phase="execution",
        ))
        m.add_technique(TacticDomain.RECONNAISSANCE, Technique(
            id="T-002", name="High", description="Test",
            severity=Severity.HIGH, kill_chain_phase="execution",
        ))
        critical = m.by_severity(Severity.CRITICAL)
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0].id, "T-001")

    def test_to_dict(self):
        m = ThreatMatrix()
        m.add_technique(TacticDomain.RECONNAISSANCE, Technique(
            id="T-001", name="Test", description="Test",
            severity=Severity.HIGH, kill_chain_phase="execution",
        ))
        d = m.to_dict()
        self.assertIn("version", d)
        self.assertIn("domains", d)
        self.assertIn("summary", d)
        self.assertEqual(d["summary"]["totalTechniques"], 1)
        self.assertEqual(d["summary"]["domains"], 1)


class TestBuildDefaultMatrix(unittest.TestCase):
    """Test the default matrix construction."""

    def test_all_11_domains_populated(self):
        m = build_default_matrix()
        for domain in TacticDomain:
            self.assertIn(domain, m.domains, f"Domain {domain} missing")
            self.assertGreater(len(m.techniques_for(domain)), 0,
                               f"Domain {domain} has no techniques")

    def test_total_technique_count(self):
        m = build_default_matrix()
        total = len(m.all_techniques())
        self.assertGreater(total, 0)
        # Each domain should have at least 4 techniques
        self.assertGreaterEqual(total, 44)

    def test_critical_techniques_exist(self):
        m = build_default_matrix()
        self.assertGreater(m.critical_count(), 0)

    def test_all_techniques_have_unique_ids(self):
        m = build_default_matrix()
        ids = [t.id for t in m.all_techniques()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_techniques_have_valid_severity(self):
        m = build_default_matrix()
        for t in m.all_techniques():
            self.assertIn(t.severity, Severity)

    def test_all_techniques_have_kill_chain_phase(self):
        m = build_default_matrix()
        for t in m.all_techniques():
            self.assertTrue(t.kill_chain_phase)

    def test_all_techniques_have_indicators(self):
        m = build_default_matrix()
        for t in m.all_techniques():
            self.assertGreater(len(t.indicators), 0,
                               f"Technique {t.id} has no indicators")

    def test_all_techniques_have_detection_refs(self):
        m = build_default_matrix()
        for t in m.all_techniques():
            self.assertGreater(len(t.detection_refs), 0,
                               f"Technique {t.id} has no detection refs")

    def test_all_techniques_have_mitigation_refs(self):
        m = build_default_matrix()
        for t in m.all_techniques():
            self.assertGreater(len(t.mitigation_refs), 0,
                               f"Technique {t.id} has no mitigation refs")

    def test_prerequisites_reference_existing_techniques(self):
        m = build_default_matrix()
        all_ids = {t.id for t in m.all_techniques()}
        for t in m.all_techniques():
            for prereq in t.prerequisites:
                self.assertIn(prereq, all_ids,
                              f"Technique {t.id} has unknown prerequisite {prereq}")

    def test_serialization_round_trip(self):
        m = build_default_matrix()
        d = m.to_dict()
        # Should be JSON-serializable
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)
        # Should be deserializable
        restored = json.loads(json_str)
        self.assertEqual(restored["summary"]["totalTechniques"],
                         len(m.all_techniques()))


class TestDomainForTechnique(unittest.TestCase):
    """Test domain inference from technique ID prefix."""

    def test_all_prefixes(self):
        prefix_map = {
            "RECON": TacticDomain.RECONNAISSANCE,
            "SEMI": TacticDomain.SEMANTIC_INGRESS,
            "CTXC": TacticDomain.CONTEXT_CONTAMINATION,
            "TOOL": TacticDomain.TOOL_DISCIPLINE,
            "SBEX": TacticDomain.SANDBOX_ESCAPE,
            "PRIV": TacticDomain.PRIVILEGE_ESCALATION,
            "SWAR": TacticDomain.SWARM_CONTAGION,
            "TELX": TacticDomain.TELEMETRY_SUPPRESSION,
            "FINR": TacticDomain.FINANCIAL_RAIL,
            "EXFX": TacticDomain.STATE_EXFILTRATION,
            "RSRX": TacticDomain.RESOURCE_EXHAUSTION,
        }
        for prefix, expected_domain in prefix_map.items():
            t = Technique(
                id=f"{prefix}-001", name="Test", description="Test",
                severity=Severity.HIGH, kill_chain_phase="execution",
            )
            self.assertEqual(_domain_for_technique(t), expected_domain)


class TestEmulationResult(unittest.TestCase):
    """Test EmulationResult dataclass."""

    def test_creation(self):
        r = EmulationResult(
            technique_id="TEST-001",
            domain=TacticDomain.RECONNAISSANCE,
            status=EmulationStatus.SUCCESS,
            severity=Severity.HIGH,
            description="Test",
            simulated_action="Test action",
            expected_detection="DETECT-001",
            expected_mitigation="MITIG-001",
        )
        self.assertEqual(r.technique_id, "TEST-001")
        self.assertEqual(r.status, EmulationStatus.SUCCESS)

    def test_to_dict(self):
        r = EmulationResult(
            technique_id="TEST-001",
            domain=TacticDomain.RECONNAISSANCE,
            status=EmulationStatus.BLOCKED,
            severity=Severity.HIGH,
            description="Test",
            simulated_action="Test action",
            expected_detection="DETECT-001",
            expected_mitigation="MITIG-001",
        )
        d = r.to_dict()
        self.assertEqual(d["techniqueId"], "TEST-001")
        self.assertEqual(d["status"], "blocked")
        self.assertEqual(d["domain"], "reconnaissance")


class TestEmulationReport(unittest.TestCase):
    """Test EmulationReport aggregation."""

    def test_empty_report(self):
        r = EmulationReport()
        self.assertEqual(r.total_techniques, 0)
        self.assertEqual(r.successful, 0)
        self.assertEqual(r.blocked, 0)
        self.assertEqual(r.detected, 0)
        self.assertEqual(r.critical_gaps, [])

    def test_report_aggregation(self):
        results = [
            EmulationResult("T-001", TacticDomain.RECONNAISSANCE,
                            EmulationStatus.SUCCESS, Severity.CRITICAL,
                            "Test", "Action", "D-001", "M-001"),
            EmulationResult("T-002", TacticDomain.RECONNAISSANCE,
                            EmulationStatus.BLOCKED, Severity.HIGH,
                            "Test", "Action", "D-002", "M-002"),
            EmulationResult("T-003", TacticDomain.RECONNAISSANCE,
                            EmulationStatus.DETECTED, Severity.HIGH,
                            "Test", "Action", "D-003", "M-003"),
        ]
        r = EmulationReport(results=results)
        self.assertEqual(r.total_techniques, 3)
        self.assertEqual(r.successful, 1)
        self.assertEqual(r.blocked, 1)
        self.assertEqual(r.detected, 1)
        self.assertEqual(len(r.critical_gaps), 1)

    def test_by_domain(self):
        results = [
            EmulationResult("T-001", TacticDomain.RECONNAISSANCE,
                            EmulationStatus.SUCCESS, Severity.HIGH,
                            "Test", "Action", "D-001", "M-001"),
            EmulationResult("T-002", TacticDomain.SEMANTIC_INGRESS,
                            EmulationStatus.BLOCKED, Severity.HIGH,
                            "Test", "Action", "D-002", "M-002"),
        ]
        r = EmulationReport(results=results)
        recon = r.by_domain(TacticDomain.RECONNAISSANCE)
        self.assertEqual(len(recon), 1)
        self.assertEqual(recon[0].technique_id, "T-001")

    def test_to_dict(self):
        r = EmulationReport(results=[
            EmulationResult("T-001", TacticDomain.RECONNAISSANCE,
                            EmulationStatus.SUCCESS, Severity.HIGH,
                            "Test", "Action", "D-001", "M-001"),
        ])
        d = r.to_dict()
        self.assertIn("summary", d)
        self.assertIn("results", d)
        self.assertEqual(d["summary"]["totalTechniques"], 1)


class TestAdversaryEmulator(unittest.TestCase):
    """Test the adversary emulation engine."""

    def setUp(self):
        self.emulator = AdversaryEmulator()

    def test_emulate_technique(self):
        t = Technique(
            id="RECON-001", name="Test", description="Test",
            severity=Severity.HIGH, kill_chain_phase="execution",
        )
        result = self.emulator.emulate_technique(t)
        self.assertIsInstance(result, EmulationResult)
        self.assertEqual(result.technique_id, "RECON-001")

    def test_emulate_domain(self):
        results = self.emulator.emulate_domain(TacticDomain.RECONNAISSANCE)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.domain, TacticDomain.RECONNAISSANCE)

    def test_emulate_all(self):
        report = self.emulator.emulate_all()
        self.assertIsInstance(report, EmulationReport)
        self.assertGreater(report.total_techniques, 0)
        # Should cover all 11 domains
        domains_covered = {r.domain for r in report.results}
        self.assertEqual(len(domains_covered), 11)

    def test_custom_handler(self):
        called = []

        def custom_handler(technique):
            called.append(technique.id)
            return EmulationResult(
                technique_id=technique.id,
                domain=TacticDomain.RECONNAISSANCE,
                status=EmulationStatus.BLOCKED,
                severity=technique.severity,
                description=technique.description,
                simulated_action="Custom",
                expected_detection="DETECT-001",
                expected_mitigation="MITIG-001",
            )

        self.emulator.register_handler("RECON-001", custom_handler)
        t = Technique(
            id="RECON-001", name="Test", description="Test",
            severity=Severity.HIGH, kill_chain_phase="execution",
        )
        result = self.emulator.emulate_technique(t)
        self.assertEqual(result.status, EmulationStatus.BLOCKED)
        self.assertEqual(called, ["RECON-001"])

    def test_report_serialization(self):
        report = self.emulator.emulate_all()
        d = report.to_dict()
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)


class TestDetectionRules(unittest.TestCase):
    """Test detection rules."""

    def test_build_detection_rules(self):
        rules = build_detection_rules()
        self.assertGreater(len(rules), 0)
        for rule in rules:
            self.assertIsInstance(rule, DetectionRule)
            self.assertTrue(rule.id.startswith("DETECT-"))

    def test_detection_rule_count_matches_techniques(self):
        matrix = build_default_matrix()
        rules = build_detection_rules()
        # Each technique should have at least one detection rule
        technique_ids = {t.id for t in matrix.all_techniques()}
        covered_ids = set()
        for rule in rules:
            covered_ids.update(rule.technique_ids)
        self.assertEqual(technique_ids, covered_ids)

    def test_detection_rule_to_dict(self):
        rules = build_detection_rules()
        d = rules[0].to_dict()
        self.assertIn("id", d)
        self.assertIn("techniqueIds", d)
        self.assertIn("domain", d)


class TestMitigations(unittest.TestCase):
    """Test mitigations."""

    def test_build_mitigations(self):
        mitigations = build_mitigations()
        self.assertGreater(len(mitigations), 0)
        for m in mitigations:
            self.assertIsInstance(m, Mitigation)
            self.assertTrue(m.id.startswith("MITIG-"))

    def test_mitigation_count_matches_techniques(self):
        matrix = build_default_matrix()
        mitigations = build_mitigations()
        technique_ids = {t.id for t in matrix.all_techniques()}
        covered_ids = set()
        for m in mitigations:
            covered_ids.update(m.technique_ids)
        self.assertEqual(technique_ids, covered_ids)

    def test_mitigation_to_dict(self):
        mitigations = build_mitigations()
        d = mitigations[0].to_dict()
        self.assertIn("id", d)
        self.assertIn("techniqueIds", d)
        self.assertIn("effectiveness", d)


class TestMatrixCompleteness(unittest.TestCase):
    """Verify the matrix covers all required tactic domains."""

    def setUp(self):
        self.matrix = build_default_matrix()

    def test_reconnaissance_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.RECONNAISSANCE)), 4)

    def test_semantic_ingress_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.SEMANTIC_INGRESS)), 4)

    def test_context_contamination_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.CONTEXT_CONTAMINATION)), 4)

    def test_tool_discipline_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.TOOL_DISCIPLINE)), 4)

    def test_sandbox_escape_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.SANDBOX_ESCAPE)), 4)

    def test_privilege_escalation_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.PRIVILEGE_ESCALATION)), 4)

    def test_swarm_contagion_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.SWARM_CONTAGION)), 4)

    def test_telemetry_suppression_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.TELEMETRY_SUPPRESSION)), 4)

    def test_financial_rail_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.FINANCIAL_RAIL)), 4)

    def test_state_exfiltration_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.STATE_EXFILTRATION)), 4)

    def test_resource_exhaustion_has_4_techniques(self):
        self.assertGreaterEqual(
            len(self.matrix.techniques_for(TacticDomain.RESOURCE_EXHAUSTION)), 4)


class TestKillChainCoverage(unittest.TestCase):
    """Verify techniques span the full kill chain."""

    def test_kill_chain_phases_present(self):
        matrix = build_default_matrix()
        phases = {t.kill_chain_phase for t in matrix.all_techniques()}
        expected_phases = {
            "reconnaissance", "delivery", "persistence", "execution",
            "privilege_escalation", "credential_access", "lateral_movement",
            "command_and_control", "exfiltration", "impact",
            "defense_evasion",
        }
        # At least these core phases should be present
        self.assertTrue(phases.issubset(expected_phases | {"delivery", "persistence"}))
        self.assertIn("reconnaissance", phases)
        self.assertIn("execution", phases)
        self.assertIn("impact", phases)


if __name__ == "__main__":
    unittest.main()
