"""Policy engine for safe OmniSwarm action execution (P6)."""

from __future__ import annotations

import base64
import binascii
import re
import string
import unicodedata
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    risk_level: RiskLevel
    reason: str


class PolicyEngine:
    """Deny-by-default policy gate for node actions and task intents."""

    DEFAULT_ALLOWED_ACTIONS = {
        "create_swarm",
        "read_result",
        "p2p_heartbeat",
        "telemetry_emit",
        "evolution_step",
    }

    HIGH_RISK_KEYWORDS = {
        "ransomware",
        "malware",
        "wipe disk",
        "format c:",
        "rm -rf",
        "delete all files",
        "steal credentials",
        "exfiltrate",
        "ddos",
        "keylogger",
    }

    MEDIUM_RISK_KEYWORDS = {
        "send email",
        "calendar",
        "deploy",
        "run shell",
        "api write",
        "drone",
        "execute command",
    }

    HIGH_RISK_PATTERNS = [
        re.compile(r"\brm\s+-rf\b"),
        re.compile(r"\bformat\s+c:\b"),
        re.compile(r"\b(del|erase)\s+/[sq]\b"),
        re.compile(r"\bpowershell\s+-enc\b"),
        re.compile(r"\bcurl\b.*\|\s*(bash|sh|powershell)\b"),
        re.compile(r"\b(downloadstring|iex|invoke-expression)\b"),
    ]

    MEDIUM_RISK_PATTERNS = [
        re.compile(r"\b(send|compose)\s+email\b"),
        re.compile(r"\b(run|execute)\s+(shell|command)\b"),
        re.compile(r"\bdeploy\b"),
        re.compile(r"\b(api|db)\s+write\b"),
    ]

    def __init__(
        self,
        allow_medium_risk: bool = False,
        allowed_actions: set[str] | None = None,
    ):
        self.allow_medium_risk = allow_medium_risk
        self.allowed_actions = (
            set(allowed_actions)
            if allowed_actions is not None
            else set(self.DEFAULT_ALLOWED_ACTIONS)
        )

    @staticmethod
    def _is_mostly_printable(text: str) -> bool:
        if not text:
            return False
        printable_count = sum(ch in string.printable for ch in text)
        return printable_count / len(text) >= 0.85

    def normalize_task_text(self, task: str) -> str:
        """Normalize and enrich text for obfuscation-aware policy checks."""
        raw = (task or "").strip()
        if not raw:
            return ""

        normalized_source = unicodedata.normalize("NFKC", raw).strip()
        normalized = normalized_source.casefold()
        normalized = re.sub(r"\s+", " ", normalized).strip()
        candidates = [normalized]

        # Attempt base64 decode on long base64-like chunks.
        base64_chunks = re.findall(r"(?:[a-zA-Z0-9+/]{8,}={0,2})", normalized_source)
        for chunk in base64_chunks:
            if len(chunk) % 4 != 0:
                continue
            try:
                decoded_bytes = base64.b64decode(chunk, validate=True)
            except (binascii.Error, ValueError):
                continue
            try:
                decoded = decoded_bytes.decode("utf-8", errors="ignore")
            except Exception:
                continue
            decoded = unicodedata.normalize("NFKC", decoded).casefold().strip()
            if decoded and self._is_mostly_printable(decoded):
                candidates.append(decoded)

        # Attempt hex decode for 0x... or dense hex segments.
        hex_chunks = re.findall(r"\b(?:0x)?[0-9a-f]{8,}\b", normalized)
        for chunk in hex_chunks:
            hex_text = chunk[2:] if chunk.startswith("0x") else chunk
            if len(hex_text) % 2 != 0:
                continue
            try:
                decoded = bytes.fromhex(hex_text).decode("utf-8", errors="ignore")
            except ValueError:
                continue
            decoded = unicodedata.normalize("NFKC", decoded).casefold().strip()
            if decoded and self._is_mostly_printable(decoded):
                candidates.append(decoded)

        merged = " ".join(candidates)
        # Remove punctuation separators so split obfuscations like "r m - r f" are detectable.
        merged = re.sub(r"[^a-z0-9]+", " ", merged)
        merged = re.sub(r"\s+", " ", merged).strip()
        return merged

    def classify_task_risk(self, task: str) -> RiskLevel:
        text = self.normalize_task_text(task)
        compact = text.replace(" ", "")

        if "rmrf" in compact or "formatc" in compact or "deleteallfiles" in compact:
            return RiskLevel.HIGH

        for pattern in self.HIGH_RISK_PATTERNS:
            if pattern.search(text):
                return RiskLevel.HIGH
        if any(keyword in text for keyword in self.HIGH_RISK_KEYWORDS):
            return RiskLevel.HIGH

        for pattern in self.MEDIUM_RISK_PATTERNS:
            if pattern.search(text):
                return RiskLevel.MEDIUM
        if any(keyword in text for keyword in self.MEDIUM_RISK_KEYWORDS):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def evaluate(self, action: str, task: str = "") -> PolicyDecision:
        if action not in self.allowed_actions:
            return PolicyDecision(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                reason=f"Action '{action}' is not allowlisted.",
            )

        risk = self.classify_task_risk(task)
        if risk == RiskLevel.HIGH:
            return PolicyDecision(
                allowed=False,
                risk_level=risk,
                reason="High-risk intent blocked by policy.",
            )
        if risk == RiskLevel.MEDIUM and not self.allow_medium_risk:
            return PolicyDecision(
                allowed=False,
                risk_level=risk,
                reason="Medium-risk intent requires explicit approval.",
            )

        return PolicyDecision(
            allowed=True,
            risk_level=risk,
            reason="Allowed by policy.",
        )
