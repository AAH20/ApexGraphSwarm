"""Tests for the red team framework."""
import json
import tempfile
import unittest
from pathlib import Path

from kernels.red_team import (
    RedTeamOrchestrator,
    RedTeamConfig,
    RedTeamResult,
    AttackSurface,
    SurfaceType,
    Vulnerability,
    Severity,
    ExploitChain,
    ChainStep,
    ChainStepStatus,
    DisclosureReport,
    DisclosureStage,
    discover_all_surfaces,
    discover_vulnerabilities,
    build_exploit_chains,
    create_disclosure_report,
    generate_disclosure_summary,
    get_disclosure_recommendations,
    run_red_team,
)


class TestAttackSurface(unittest.TestCase):
    def test_discover_all_surfaces(self):
        surfaces = discover_all_surfaces()
        self.assertGreater(len(surfaces), 0)
        for surface in surfaces:
            self.assertIsInstance(surface, AttackSurface)
            self.assertIsInstance(surface.surface_type, SurfaceType)
            self.assertTrue(surface.name)
            self.assertTrue(surface.description)

    def test_surface_to_dict(self):
        surface = AttackSurface(
            name="test",
            surface_type=SurfaceType.CONTROL_API,
            description="Test surface",
            attack_vectors=["vector1"],
            mitigations=["mitigation1"],
        )
        data = surface.to_dict()
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["surfaceType"], "control_api")
        self.assertEqual(data["attackVectors"], ["vector1"])
        self.assertEqual(data["mitigations"], ["mitigation1"])

    def test_surface_types_exist(self):
        surfaces = discover_all_surfaces()
        types = {s.surface_type for s in surfaces}
        self.assertIn(SurfaceType.CONTROL_API, types)
        self.assertIn(SurfaceType.IDENTITY, types)
        self.assertIn(SurfaceType.ACCESS_GRANT, types)
        self.assertIn(SurfaceType.BUDGET, types)
        self.assertIn(SurfaceType.LEASE, types)
        self.assertIn(SurfaceType.SPECIALIST_CONTRACT, types)
        self.assertIn(SurfaceType.CHECKPOINT, types)
        self.assertIn(SurfaceType.RECONCILIATION, types)


class TestVulnerability(unittest.TestCase):
    def test_discover_vulnerabilities(self):
        surfaces = discover_all_surfaces()
        vulns = discover_vulnerabilities(surfaces)
        self.assertGreater(len(vulns), 0)
        for vuln in vulns:
            self.assertIsInstance(vuln, Vulnerability)
            self.assertIsInstance(vuln.severity, Severity)
            self.assertTrue(vuln.id)
            self.assertTrue(vuln.title)

    def test_vulnerability_to_dict(self):
        vuln = Vulnerability(
            id="RT-001",
            title="Test",
            description="Test vuln",
            severity=Severity.HIGH,
            surface_type=SurfaceType.CONTROL_API,
            attack_vector="test vector",
            impact="test impact",
            remediation="test remediation",
        )
        data = vuln.to_dict()
        self.assertEqual(data["id"], "RT-001")
        self.assertEqual(data["severity"], "high")
        self.assertEqual(data["surfaceType"], "control_api")

    def test_severity_filtering(self):
        surfaces = discover_all_surfaces()
        vulns = discover_vulnerabilities(surfaces)
        critical = [v for v in vulns if v.severity == Severity.CRITICAL]
        high = [v for v in vulns if v.severity == Severity.HIGH]
        # Just verify the filtering logic works
        self.assertIsInstance(critical, list)
        self.assertIsInstance(high, list)


class TestExploitChain(unittest.TestCase):
    def test_build_exploit_chains(self):
        surfaces = discover_all_surfaces()
        vulns = discover_vulnerabilities(surfaces)
        chains = build_exploit_chains(vulns)
        self.assertIsInstance(chains, list)
        for chain in chains:
            self.assertIsInstance(chain, ExploitChain)
            self.assertTrue(chain.id)
            self.assertTrue(chain.name)
            self.assertGreater(len(chain.steps), 0)

    def test_chain_step_to_dict(self):
        step = ChainStep(
            order=1,
            vulnerability_id="RT-001",
            description="Test step",
            prerequisites=[],
        )
        data = step.to_dict()
        self.assertEqual(data["order"], 1)
        self.assertEqual(data["vulnerabilityId"], "RT-001")
        self.assertEqual(data["status"], "pending")

    def test_chain_to_dict(self):
        chain = ExploitChain(
            id="CHAIN-001",
            name="Test chain",
            description="Test description",
            steps=[ChainStep(order=1, vulnerability_id="RT-001", description="Step 1")],
            overall_severity=Severity.HIGH,
            impact="Test impact",
        )
        data = chain.to_dict()
        self.assertEqual(data["id"], "CHAIN-001")
        self.assertEqual(data["overallSeverity"], "high")
        self.assertEqual(len(data["steps"]), 1)


class TestDisclosure(unittest.TestCase):
    def test_create_disclosure_report(self):
        surfaces = discover_all_surfaces()
        vulns = discover_vulnerabilities(surfaces)
        chains = build_exploit_chains(vulns)
        report = create_disclosure_report(vulns, chains)
        self.assertIsInstance(report, DisclosureReport)
        self.assertTrue(report.id)
        self.assertEqual(report.stage, DisclosureStage.DISCOVERED)
        self.assertGreater(len(report.vulnerabilities), 0)

    def test_disclosure_report_to_dict(self):
        surfaces = discover_all_surfaces()
        vulns = discover_vulnerabilities(surfaces)
        chains = build_exploit_chains(vulns)
        report = create_disclosure_report(vulns, chains)
        data = report.to_dict()
        self.assertIn("id", data)
        self.assertIn("stage", data)
        self.assertIn("vulnerabilities", data)
        self.assertIn("exploitChains", data)

    def test_disclosure_stage_advance(self):
        report = DisclosureReport(
            id="RD-001",
            title="Test",
            reporter="test",
            discovered_at=__import__("datetime").datetime.utcnow(),
            stage=DisclosureStage.DISCOVERED,
        )
        new_stage = report.advance_stage()
        self.assertEqual(new_stage, DisclosureStage.REPORTED)

    def test_disclosure_timeline(self):
        report = DisclosureReport(
            id="RD-001",
            title="Test",
            reporter="test",
            discovered_at=__import__("datetime").datetime.utcnow(),
            stage=DisclosureStage.DISCOVERED,
        )
        report.add_timeline_entry("Test event", "Test details")
        self.assertEqual(len(report.remediation_timeline), 1)
        self.assertEqual(report.remediation_timeline[0]["event"], "Test event")

    def test_generate_disclosure_summary(self):
        surfaces = discover_all_surfaces()
        vulns = discover_vulnerabilities(surfaces)
        chains = build_exploit_chains(vulns)
        report = create_disclosure_report(vulns, chains)
        summary = generate_disclosure_summary(report)
        self.assertIn("Disclosure Report:", summary)
        self.assertIn("Vulnerabilities:", summary)

    def test_get_disclosure_recommendations(self):
        report = DisclosureReport(
            id="RD-001",
            title="Test",
            reporter="test",
            discovered_at=__import__("datetime").datetime.utcnow(),
            stage=DisclosureStage.DISCOVERED,
        )
        recs = get_disclosure_recommendations(report)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)


class TestRedTeamOrchestrator(unittest.TestCase):
    def test_orchestrator_run(self):
        config = RedTeamConfig(
            max_vulnerabilities=50,
            min_severity=Severity.LOW,
            generate_chains=True,
            generate_disclosure=True,
        )
        orchestrator = RedTeamOrchestrator(config)
        result = orchestrator.run()
        self.assertIsInstance(result, RedTeamResult)
        self.assertGreater(len(result.surfaces), 0)
        self.assertGreater(len(result.vulnerabilities), 0)
        self.assertIsNotNone(result.completed_at)

    def test_orchestrator_summary(self):
        config = RedTeamConfig(
            max_vulnerabilities=50,
            min_severity=Severity.LOW,
        )
        orchestrator = RedTeamOrchestrator(config)
        result = orchestrator.run()
        summary = result.summary()
        self.assertIn("target", summary)
        self.assertIn("surfacesDiscovered", summary)
        self.assertIn("vulnerabilitiesFound", summary)
        self.assertIn("severityBreakdown", summary)

    def test_orchestrator_export_json(self):
        config = RedTeamConfig(
            max_vulnerabilities=10,
            min_severity=Severity.LOW,
            output_dir=tempfile.gettempdir(),
        )
        orchestrator = RedTeamOrchestrator(config)
        orchestrator.run()
        path = orchestrator.export_json()
        self.assertTrue(Path(path).exists())
        with open(path) as f:
            data = json.load(f)
        self.assertIn("surfaces", data)
        self.assertIn("vulnerabilities", data)

    def test_orchestrator_export_markdown(self):
        config = RedTeamConfig(
            max_vulnerabilities=10,
            min_severity=Severity.LOW,
            output_dir=tempfile.gettempdir(),
        )
        orchestrator = RedTeamOrchestrator(config)
        orchestrator.run()
        path = orchestrator.export_markdown()
        self.assertTrue(Path(path).exists())
        content = Path(path).read_text()
        self.assertIn("# Red Team Assessment:", content)

    def test_orchestrator_filter_by_severity(self):
        config = RedTeamConfig(
            max_vulnerabilities=100,
            min_severity=Severity.HIGH,
        )
        orchestrator = RedTeamOrchestrator(config)
        result = orchestrator.run()
        for vuln in result.vulnerabilities:
            self.assertIn(vuln.severity, [Severity.CRITICAL, Severity.HIGH])

    def test_orchestrator_max_vulnerabilities(self):
        config = RedTeamConfig(
            max_vulnerabilities=5,
            min_severity=Severity.LOW,
        )
        orchestrator = RedTeamOrchestrator(config)
        result = orchestrator.run()
        self.assertLessEqual(len(result.vulnerabilities), 5)

    def test_run_red_team_convenience(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_red_team(
                max_vulnerabilities=10,
                min_severity=Severity.LOW,
                output_dir=tmpdir,
                export_json=True,
                export_markdown=True,
            )
            self.assertIsInstance(result, RedTeamResult)
            self.assertGreater(len(result.vulnerabilities), 0)


class TestRedTeamIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        """Test the complete red team pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_red_team(
                max_vulnerabilities=50,
                min_severity=Severity.LOW,
                include_info=True,
                generate_chains=True,
                generate_disclosure=True,
                output_dir=tmpdir,
                export_json=True,
                export_markdown=True,
            )

            # Verify result structure
            self.assertIsInstance(result, RedTeamResult)
            self.assertGreater(len(result.surfaces), 0)
            self.assertGreater(len(result.vulnerabilities), 0)
            self.assertIsNotNone(result.disclosure_report)

            # Verify exports
            json_files = list(Path(tmpdir).glob("red-team-*.json"))
            md_files = list(Path(tmpdir).glob("red-team-*.md"))
            self.assertGreater(len(json_files), 0)
            self.assertGreater(len(md_files), 0)

            # Verify JSON content
            with open(json_files[0]) as f:
                data = json.load(f)
            self.assertIn("surfaces", data)
            self.assertIn("vulnerabilities", data)
            self.assertIn("exploitChains", data)
            self.assertIn("disclosureReport", data)

            # Verify Markdown content
            md_content = md_files[0].read_text()
            self.assertIn("# Red Team Assessment:", md_content)
            self.assertIn("## Vulnerabilities", md_content)


if __name__ == "__main__":
    unittest.main()
