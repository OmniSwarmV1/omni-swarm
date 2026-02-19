"""Policy engine for safe OmniSwarm action execution (P6)."""

from __future__ import annotations

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

    def classify_task_risk(self, task: str) -> RiskLevel:
        text = (task or "").lower()
        if any(keyword in text for keyword in self.HIGH_RISK_KEYWORDS):
            return RiskLevel.HIGH
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
