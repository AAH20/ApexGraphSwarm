"""On-chain settlement adapter for ETH and ERC-20 token payouts.

Provides an abstract SettlementAdapter interface and a MockSettlementAdapter
for testing. Production implementations would use web3.py or similar.
"""
from __future__ import annotations

import hashlib
import secrets
import time
from abc import ABC, abstractmethod
from typing import Any

from .types import AssetType, Settlement


class SettlementError(ValueError):
    """Invalid settlement operation."""


class SettlementAdapter(ABC):
    """Abstract interface for on-chain settlement."""

    @abstractmethod
    def settle_eth(
        self,
        *,
        escrow_id: str,
        recipient: str,
        amount: int,
        milestone_index: int | None = None,
    ) -> Settlement:
        """Settle an ETH payout. Returns a Settlement record."""
        ...

    @abstractmethod
    def settle_erc20(
        self,
        *,
        escrow_id: str,
        token_address: str,
        recipient: str,
        amount: int,
        milestone_index: int | None = None,
    ) -> Settlement:
        """Settle an ERC-20 token payout. Returns a Settlement record."""
        ...

    @abstractmethod
    def get_balance(self, address: str, asset_type: AssetType, token_address: str | None = None) -> int:
        """Get the balance of an address for a given asset."""
        ...

    @abstractmethod
    def get_transaction_receipt(self, tx_hash: str) -> dict[str, Any] | None:
        """Get transaction receipt by hash."""
        ...


class MockSettlementAdapter(SettlementAdapter):
    """In-memory mock settlement adapter for testing.

    Simulates on-chain behavior without requiring a blockchain connection.
    Tracks balances and generates fake transaction hashes.
    """

    def __init__(self, *, clock=time.time, confirmations_required: int = 1):
        self._clock = clock
        self._confirmations_required = confirmations_required
        self._balances: dict[tuple[str, AssetType, str | None], int] = {}
        self._transactions: dict[str, dict[str, Any]] = {}
        self._settlements: dict[str, Settlement] = {}
        self._block_number = 1000

    def settle_eth(
        self,
        *,
        escrow_id: str,
        recipient: str,
        amount: int,
        milestone_index: int | None = None,
    ) -> Settlement:
        return self._settle(
            escrow_id=escrow_id,
            recipient=recipient,
            amount=amount,
            asset_type=AssetType.ETH,
            token_address=None,
            milestone_index=milestone_index,
        )

    def settle_erc20(
        self,
        *,
        escrow_id: str,
        token_address: str,
        recipient: str,
        amount: int,
        milestone_index: int | None = None,
    ) -> Settlement:
        if not token_address:
            raise SettlementError("Token address is required for ERC-20 settlement.")
        return self._settle(
            escrow_id=escrow_id,
            recipient=recipient,
            amount=amount,
            asset_type=AssetType.ERC20,
            token_address=token_address,
            milestone_index=milestone_index,
        )

    def get_balance(self, address: str, asset_type: AssetType, token_address: str | None = None) -> int:
        key = (address, asset_type, token_address)
        return self._balances.get(key, 0)

    def get_transaction_receipt(self, tx_hash: str) -> dict[str, Any] | None:
        return self._transactions.get(tx_hash)

    def get_settlement(self, settlement_id: str) -> Settlement | None:
        return self._settlements.get(settlement_id)

    def list_settlements(self) -> list[Settlement]:
        return list(self._settlements.values())

    def set_balance(
        self, address: str, asset_type: AssetType, amount: int, token_address: str | None = None
    ) -> None:
        """Set a balance directly (for testing)."""
        key = (address, asset_type, token_address)
        self._balances[key] = amount

    def _settle(
        self,
        *,
        escrow_id: str,
        recipient: str,
        amount: int,
        asset_type: AssetType,
        token_address: str | None,
        milestone_index: int | None,
    ) -> Settlement:
        if amount <= 0:
            raise SettlementError("Settlement amount must be positive.")
        if not recipient:
            raise SettlementError("Recipient address is required.")

        settlement_id = self._generate_id("settlement")
        tx_hash = self._generate_tx_hash()
        self._block_number += 1

        # Update balance
        key = (recipient, asset_type, token_address)
        current = self._balances.get(key, 0)
        self._balances[key] = current + amount

        # Record transaction
        self._transactions[tx_hash] = {
            "txHash": tx_hash,
            "from": "escrow_contract",
            "to": recipient,
            "amount": amount,
            "assetType": asset_type.value,
            "tokenAddress": token_address,
            "blockNumber": self._block_number,
            "timestamp": self._clock(),
            "confirmations": self._confirmations_required,
            "status": "confirmed",
        }

        settlement = Settlement(
            settlement_id=settlement_id,
            escrow_id=escrow_id,
            milestone_index=milestone_index,
            recipient=recipient,
            amount=amount,
            asset_type=asset_type,
            token_address=token_address,
            tx_hash=tx_hash,
            settled_at=self._clock(),
            block_number=self._block_number,
        )
        self._settlements[settlement_id] = settlement
        return settlement

    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}_{secrets.token_hex(16)}"

    @staticmethod
    def _generate_tx_hash() -> str:
        return "0x" + secrets.token_hex(32)
