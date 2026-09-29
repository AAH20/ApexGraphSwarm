"""DID-bound identity for agents.

Implements a simplified Decentralized Identifier (DID) system where
each agent has a unique DID that binds to a DID Document containing
public keys, service endpoints, and authentication methods.

DID format: did:apex:<method-specific-id>
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any


class DIDError(ValueError):
    """DID parsing, validation, or resolution error."""


@dataclass(frozen=True)
class DID:
    """A Decentralized Identifier."""
    method: str
    method_specific_id: str

    # Valid DID pattern: did:method:id
    PREFIX = "did"
    SUPPORTED_METHODS = {"apex", "web", "key"}

    def __str__(self) -> str:
        return f"did:{self.method}:{self.method_specific_id}"

    def __repr__(self) -> str:
        return f"DID('{str(self)}')"

    @classmethod
    def parse(cls, did_string: str) -> DID:
        """Parse a DID string into a DID object."""
        if not isinstance(did_string, str):
            raise DIDError("DID must be a string")
        parts = did_string.split(":")
        if len(parts) < 3:
            raise DIDError(f"Invalid DID format: '{did_string}'. Expected 'did:method:id'")
        if parts[0] != cls.PREFIX:
            raise DIDError(f"Invalid DID prefix: '{parts[0]}'. Expected 'did'")
        method = parts[1]
        if method not in cls.SUPPORTED_METHODS:
            raise DIDError(f"Unsupported DID method: '{method}'")
        method_specific_id = ":".join(parts[2:])
        if not method_specific_id:
            raise DIDError("DID method-specific-id must not be empty")
        return cls(method=method, method_specific_id=method_specific_id)

    @classmethod
    def create(cls, method: str = "apex", method_specific_id: str | None = None) -> DID:
        """Create a new DID, optionally with a generated ID."""
        if method not in cls.SUPPORTED_METHODS:
            raise DIDError(f"Unsupported DID method: '{method}'")
        if method_specific_id is None:
            method_specific_id = cls._generate_id(method)
        return cls(method=method, method_specific_id=method_specific_id)

    @classmethod
    def _generate_id(cls, method: str) -> str:
        """Generate a method-specific identifier."""
        if method == "apex":
            # 32 hex chars from 16 random bytes
            return secrets.token_hex(16)
        elif method == "key":
            # Base64url-encoded public key hash
            raw = secrets.token_bytes(32)
            import base64
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
        else:
            return secrets.token_urlsafe(24)

    def to_dict(self) -> dict[str, str]:
        return {"did": str(self)}


@dataclass
class DIDDocument:
    """A DID Document containing public keys and service endpoints."""
    did: DID
    context: list[str] = field(default_factory=lambda: ["https://www.w3.org/ns/did/v1"])
    verification_methods: list[dict[str, Any]] = field(default_factory=list)
    authentication: list[str] = field(default_factory=list)
    service_endpoints: list[dict[str, Any]] = field(default_factory=list)
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)

    def add_verification_method(self, method_id: str, method_type: str,
                                 controller: str, public_key: str) -> None:
        """Add a verification method (public key) to the document."""
        vm = {
            "id": f"{self.did}#{method_id}",
            "type": method_type,
            "controller": controller,
            "publicKeyHex": public_key,
        }
        self.verification_methods.append(vm)
        self.authentication.append(vm["id"])
        self.updated = time.time()

    def add_service(self, service_id: str, service_type: str,
                    endpoint: str) -> None:
        """Add a service endpoint to the document."""
        svc = {
            "id": f"{self.did}#{service_id}",
            "type": service_type,
            "serviceEndpoint": endpoint,
        }
        self.service_endpoints.append(svc)
        self.updated = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "@context": self.context,
            "id": str(self.did),
            "verificationMethod": self.verification_methods,
            "authentication": self.authentication,
            "service": self.service_endpoints,
            "created": self.created,
            "updated": self.updated,
        }

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DIDDocument:
        """Parse a DID Document from a dictionary."""
        did = DID.parse(data["id"])
        doc = cls(
            did=did,
            context=data.get("@context", ["https://www.w3.org/ns/did/v1"]),
            created=data.get("created", time.time()),
            updated=data.get("updated", time.time()),
        )
        for vm in data.get("verificationMethod", []):
            doc.verification_methods.append(vm)
        doc.authentication = list(data.get("authentication", []))
        for svc in data.get("service", []):
            doc.service_endpoints.append(svc)
        return doc

    @classmethod
    def from_json(cls, json_str: str) -> DIDDocument:
        """Parse a DID Document from a JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise DIDError(f"Invalid JSON in DID Document: {e}") from e
        return cls.from_dict(data)


class DIDResolver:
    """Resolves DIDs to DID Documents.

    In a production system, this would query a blockchain or distributed
    ledger. Here we use an in-memory store with optional persistence.
    """

    def __init__(self):
        self._documents: dict[str, DIDDocument] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(self, document: DIDDocument, *,
                 metadata: dict[str, Any] | None = None) -> None:
        """Register a DID Document for resolution."""
        did_str = str(document.did)
        self._documents[did_str] = document
        self._metadata[did_str] = metadata or {}

    def resolve(self, did: DID | str) -> DIDDocument | None:
        """Resolve a DID to its Document. Returns None if not found."""
        did_str = str(did) if isinstance(did, DID) else did
        return self._documents.get(did_str)

    def resolve_required(self, did: DID | str) -> DIDDocument:
        """Resolve a DID, raising DIDError if not found."""
        doc = self.resolve(did)
        if doc is None:
            raise DIDError(f"DID not found: {did}")
        return doc

    def update_document(self, did: DID | str, document: DIDDocument) -> None:
        """Update an existing DID Document."""
        did_str = str(did) if isinstance(did, DID) else did
        if did_str not in self._documents:
            raise DIDError(f"Cannot update unknown DID: {did}")
        self._documents[did_str] = document

    def deactivate(self, did: DID | str) -> None:
        """Deactivate a DID (tombstone)."""
        did_str = str(did) if isinstance(did, DID) else did
        if did_str in self._documents:
            self._metadata[did_str]["deactivated"] = True
            self._metadata[did_str]["deactivated_at"] = time.time()

    def is_deactivated(self, did: DID | str) -> bool:
        did_str = str(did) if isinstance(did, DID) else did
        return self._metadata.get(did_str, {}).get("deactivated", False)

    def list_dids(self) -> list[str]:
        """List all registered DIDs."""
        return sorted(self._documents.keys())

    def verify_ownership(self, did: DID | str, proof: dict[str, Any]) -> bool:
        """Verify that a proof of ownership is valid for a DID.

        The proof must contain a signature made with one of the DID's
        verification methods over a challenge.
        """
        doc = self.resolve(did)
        if doc is None:
            return False
        if self.is_deactivated(did):
            return False

        # Simplified: check that proof references a valid verification method
        vm_id = proof.get("verificationMethod")
        if not vm_id:
            return False
        valid_ids = {vm["id"] for vm in doc.verification_methods}
        if vm_id not in valid_ids:
            return False

        # In a real implementation, verify the cryptographic signature here
        # For now, we check the proof structure
        return (
            "challenge" in proof
            and "signature" in proof
            and proof.get("type") == "Ed25519Signature2020"
        )
