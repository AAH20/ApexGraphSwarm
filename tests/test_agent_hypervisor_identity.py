"""Tests for DID-bound identity."""
import json
import unittest

from kernels.agent_hypervisor.identity import (
    DID, DIDDocument, DIDError, DIDResolver,
)


class DIDTests(unittest.TestCase):
    def test_create_did(self):
        did = DID.create()
        self.assertEqual(did.method, "apex")
        self.assertTrue(did.method_specific_id)
        self.assertEqual(len(did.method_specific_id), 32)  # 16 bytes hex

    def test_create_did_with_custom_id(self):
        did = DID.create(method="apex", method_specific_id="my-id-123")
        self.assertEqual(did.method_specific_id, "my-id-123")
        self.assertEqual(str(did), "did:apex:my-id-123")

    def test_parse_valid_did(self):
        did = DID.parse("did:apex:abc123")
        self.assertEqual(did.method, "apex")
        self.assertEqual(did.method_specific_id, "abc123")

    def test_parse_did_with_colons_in_id(self):
        did = DID.parse("did:web:example.com:user:alice")
        self.assertEqual(did.method, "web")
        self.assertEqual(did.method_specific_id, "example.com:user:alice")

    def test_parse_invalid_prefix(self):
        with self.assertRaises(DIDError):
            DID.parse("notdid:apex:abc")

    def test_parse_too_few_parts(self):
        with self.assertRaises(DIDError):
            DID.parse("did:apex")

    def test_parse_empty_id(self):
        with self.assertRaises(DIDError):
            DID.parse("did:apex:")

    def test_parse_unsupported_method(self):
        with self.assertRaises(DIDError):
            DID.parse("did:unsupported:abc")

    def test_parse_non_string(self):
        with self.assertRaises(DIDError):
            DID.parse(123)

    def test_str_and_repr(self):
        did = DID.parse("did:apex:test123")
        self.assertEqual(str(did), "did:apex:test123")
        self.assertIn("did:apex:test123", repr(did))

    def test_supported_methods(self):
        self.assertIn("apex", DID.SUPPORTED_METHODS)
        self.assertIn("web", DID.SUPPORTED_METHODS)
        self.assertIn("key", DID.SUPPORTED_METHODS)

    def test_create_key_method(self):
        did = DID.create(method="key")
        self.assertEqual(did.method, "key")
        self.assertTrue(did.method_specific_id)


class DIDDocumentTests(unittest.TestCase):
    def test_create_document(self):
        did = DID.create()
        doc = DIDDocument(did=did)
        self.assertEqual(doc.did, did)
        self.assertTrue(doc.context)
        self.assertIsNotNone(doc.created)
        self.assertIsNotNone(doc.updated)

    def test_add_verification_method(self):
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_verification_method(
            method_id="key-1",
            method_type="Ed25519VerificationKey2020",
            controller=str(did),
            public_key="abcdef1234567890",
        )
        self.assertEqual(len(doc.verification_methods), 1)
        vm = doc.verification_methods[0]
        self.assertEqual(vm["id"], f"{did}#key-1")
        self.assertEqual(vm["type"], "Ed25519VerificationKey2020")
        self.assertIn(vm["id"], doc.authentication)

    def test_add_service(self):
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_service(
            service_id="agent-endpoint",
            service_type="AgentService",
            endpoint="https://example.com/agent",
        )
        self.assertEqual(len(doc.service_endpoints), 1)
        svc = doc.service_endpoints[0]
        self.assertEqual(svc["type"], "AgentService")
        self.assertEqual(svc["serviceEndpoint"], "https://example.com/agent")

    def test_to_dict(self):
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_verification_method("k1", "Ed25519VerificationKey2020", str(did), "pk")
        data = doc.to_dict()
        self.assertEqual(data["id"], str(did))
        self.assertIn("@context", data)
        self.assertEqual(len(data["verificationMethod"]), 1)

    def test_to_json_roundtrip(self):
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_verification_method("k1", "Ed25519VerificationKey2020", str(did), "pk")
        doc.add_service("s1", "AgentService", "https://example.com")
        json_str = doc.to_json()
        parsed = DIDDocument.from_json(json_str)
        self.assertEqual(parsed.did, did)
        self.assertEqual(len(parsed.verification_methods), 1)
        self.assertEqual(len(parsed.service_endpoints), 1)

    def test_from_dict(self):
        did = DID.parse("did:apex:test123")
        data = {
            "id": "did:apex:test123",
            "@context": ["https://www.w3.org/ns/did/v1"],
            "verificationMethod": [
                {"id": "did:apex:test123#k1", "type": "Ed25519VerificationKey2020",
                 "controller": "did:apex:test123", "publicKeyHex": "abc"}
            ],
            "authentication": ["did:apex:test123#k1"],
            "service": [
                {"id": "did:apex:test123#s1", "type": "AgentService",
                 "serviceEndpoint": "https://example.com"}
            ],
            "created": 1000.0,
            "updated": 2000.0,
        }
        doc = DIDDocument.from_dict(data)
        self.assertEqual(doc.did, did)
        self.assertEqual(len(doc.verification_methods), 1)
        self.assertEqual(doc.created, 1000.0)
        self.assertEqual(doc.updated, 2000.0)

    def test_from_invalid_json(self):
        with self.assertRaises(DIDError):
            DIDDocument.from_json("not json")


class DIDResolverTests(unittest.TestCase):
    def test_register_and_resolve(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        resolver.register(doc)

        resolved = resolver.resolve(did)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.did, did)

    def test_resolve_string_did(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        resolver.register(doc)

        resolved = resolver.resolve(str(did))
        self.assertIsNotNone(resolved)

    def test_resolve_not_found(self):
        resolver = DIDResolver()
        did = DID.create()
        self.assertIsNone(resolver.resolve(did))

    def test_resolve_required_raises(self):
        resolver = DIDResolver()
        did = DID.create()
        with self.assertRaises(DIDError):
            resolver.resolve_required(did)

    def test_update_document(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        resolver.register(doc)

        doc.add_verification_method("k1", "Ed25519VerificationKey2020", str(did), "pk")
        resolver.update_document(did, doc)

        updated = resolver.resolve(did)
        self.assertEqual(len(updated.verification_methods), 1)

    def test_update_unknown_did_raises(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        with self.assertRaises(DIDError):
            resolver.update_document(did, doc)

    def test_deactivate(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        resolver.register(doc)

        self.assertFalse(resolver.is_deactivated(did))
        resolver.deactivate(did)
        self.assertTrue(resolver.is_deactivated(did))

    def test_list_dids(self):
        resolver = DIDResolver()
        for _ in range(3):
            doc = DIDDocument(did=DID.create())
            resolver.register(doc)
        self.assertEqual(len(resolver.list_dids()), 3)

    def test_verify_ownership_valid(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_verification_method("k1", "Ed25519VerificationKey2020", str(did), "pk")
        resolver.register(doc)

        proof = {
            "verificationMethod": f"{did}#k1",
            "challenge": "test-challenge",
            "signature": "sig-data",
            "type": "Ed25519Signature2020",
        }
        self.assertTrue(resolver.verify_ownership(did, proof))

    def test_verify_ownership_invalid_vm(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_verification_method("k1", "Ed25519VerificationKey2020", str(did), "pk")
        resolver.register(doc)

        proof = {
            "verificationMethod": "did:apex:other#k1",
            "challenge": "test",
            "signature": "sig",
            "type": "Ed25519Signature2020",
        }
        self.assertFalse(resolver.verify_ownership(did, proof))

    def test_verify_ownership_deactivated(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        doc.add_verification_method("k1", "Ed25519VerificationKey2020", str(did), "pk")
        resolver.register(doc)
        resolver.deactivate(did)

        proof = {
            "verificationMethod": f"{did}#k1",
            "challenge": "test",
            "signature": "sig",
            "type": "Ed25519Signature2020",
        }
        self.assertFalse(resolver.verify_ownership(did, proof))

    def test_verify_ownership_no_vm_in_proof(self):
        resolver = DIDResolver()
        did = DID.create()
        doc = DIDDocument(did=did)
        resolver.register(doc)

        proof = {"challenge": "test", "signature": "sig"}
        self.assertFalse(resolver.verify_ownership(did, proof))


if __name__ == "__main__":
    unittest.main()
