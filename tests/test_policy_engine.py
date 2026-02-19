from core.policy_engine import PolicyEngine, RiskLevel


class TestPolicyEngine:
    def test_low_risk_task_allowed(self):
        engine = PolicyEngine()
        decision = engine.evaluate("create_swarm", "Optimize battery chemistry")
        assert decision.allowed is True
        assert decision.risk_level == RiskLevel.LOW

    def test_high_risk_task_blocked(self):
        engine = PolicyEngine()
        decision = engine.evaluate("create_swarm", "rm -rf all files on host")
        assert decision.allowed is False
        assert decision.risk_level == RiskLevel.HIGH

    def test_medium_risk_requires_explicit_approval(self):
        engine = PolicyEngine(allow_medium_risk=False)
        decision = engine.evaluate("create_swarm", "Send email to all contacts")
        assert decision.allowed is False
        assert decision.risk_level == RiskLevel.MEDIUM

    def test_medium_risk_allowed_when_enabled(self):
        engine = PolicyEngine(allow_medium_risk=True)
        decision = engine.evaluate("create_swarm", "Send email update")
        assert decision.allowed is True
        assert decision.risk_level == RiskLevel.MEDIUM

    def test_non_allowlisted_action_denied(self):
        engine = PolicyEngine()
        decision = engine.evaluate("shell_exec", "echo hello")
        assert decision.allowed is False

    def test_obfuscated_spaced_rm_rf_is_blocked(self):
        engine = PolicyEngine()
        decision = engine.evaluate("create_swarm", "Please run r m - r f on host")
        assert decision.allowed is False
        assert decision.risk_level == RiskLevel.HIGH

    def test_base64_obfuscated_payload_is_blocked(self):
        engine = PolicyEngine()
        # "rm -rf /" base64
        payload = "cm0gLXJmIC8="
        decision = engine.evaluate("create_swarm", f"decode and run {payload}")
        assert decision.allowed is False
        assert decision.risk_level == RiskLevel.HIGH

    def test_hex_obfuscated_payload_is_blocked(self):
        engine = PolicyEngine()
        # "rm -rf" hex
        payload = "726d202d7266"
        decision = engine.evaluate("create_swarm", f"exec {payload}")
        assert decision.allowed is False
        assert decision.risk_level == RiskLevel.HIGH

    def test_normalizer_exposes_hidden_keywords(self):
        engine = PolicyEngine()
        normalized = engine.normalize_task_text("SEND EMAIL to admins")
        assert "send email" in normalized
