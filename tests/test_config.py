"""Test configuration structures."""

import pytest
from context_harness.models import ContextConfig, AutomationConfig, RetrievalStrategy


class TestContextConfig:
    """Test ContextConfig dataclass."""

    def test_default_context_config(self):
        """Test default ContextConfig values."""
        config = ContextConfig()

        assert config.max_tokens == 4000
        assert config.sections == [
            "recent_history",
            "relevant_memories",
            "experiences",
            "system_prompt"
        ]
        assert config.retrieval_strategy == RetrievalStrategy.RECENT_FIRST
        assert "recent_history" in config.template_format
        assert "relevant_memories" in config.template_format

    def test_custom_max_tokens(self):
        """Test custom max_tokens."""
        config = ContextConfig(max_tokens=8000)

        assert config.max_tokens == 8000

    def test_custom_sections(self):
        """Test custom sections order."""
        config = ContextConfig(sections=["system_prompt", "recent_history"])

        assert config.sections == ["system_prompt", "recent_history"]

    def test_custom_retrieval_strategy(self):
        """Test custom retrieval_strategy."""
        config = ContextConfig(retrieval_strategy=RetrievalStrategy.HYBRID)

        assert config.retrieval_strategy == RetrievalStrategy.HYBRID

    def test_custom_template_format(self):
        """Test custom template_format."""
        custom_template = {
            "recent_history": "**Conversation:**\n{content}",
            "system_prompt": "SYSTEM: {content}"
        }
        config = ContextConfig(template_format=custom_template)

        assert config.template_format["recent_history"] == "**Conversation:**\n{content}"
        assert config.template_format["system_prompt"] == "SYSTEM: {content}"

    def test_template_format_keys(self):
        """Test default template_format has expected keys."""
        config = ContextConfig()

        assert "recent_history" in config.template_format
        assert "relevant_memories" in config.template_format
        assert "experiences" in config.template_format
        assert "system_prompt" in config.template_format


class TestAutomationConfig:
    """Test AutomationConfig dataclass."""

    def test_default_automation_config(self):
        """Test default AutomationConfig values."""
        config = AutomationConfig()

        # Auto-spill enabled by default
        assert config.auto_spill_messages == True
        assert config.spill_threshold_bytes == 10000

        # Auto-distill disabled by default (opt-in)
        assert config.auto_distill == False
        assert config.distill_trigger == "message_count"
        assert config.distill_threshold == 10

        # Auto-store enabled
        assert config.auto_store_memories == True
        assert config.auto_link_memories == True

    def test_disable_auto_spill(self):
        """Test disabling auto_spill_messages."""
        config = AutomationConfig(auto_spill_messages=False)

        assert config.auto_spill_messages == False

    def test_custom_spill_threshold(self):
        """Test custom spill_threshold_bytes."""
        config = AutomationConfig(spill_threshold_bytes=5000)

        assert config.spill_threshold_bytes == 5000

    def test_enable_auto_distill(self):
        """Test enabling auto_distill."""
        config = AutomationConfig(auto_distill=True)

        assert config.auto_distill == True

    def test_custom_distill_threshold(self):
        """Test custom distill_threshold."""
        config = AutomationConfig(
            auto_distill=True,
            distill_threshold=20
        )

        assert config.distill_threshold == 20

    def test_custom_distill_trigger(self):
        """Test custom distill_trigger."""
        config = AutomationConfig(distill_trigger="session_end")

        assert config.distill_trigger == "session_end"

    def test_disable_auto_store_memories(self):
        """Test disabling auto_store_memories."""
        config = AutomationConfig(auto_store_memories=False)

        assert config.auto_store_memories == False

    def test_disable_auto_link_memories(self):
        """Test disabling auto_link_memories."""
        config = AutomationConfig(auto_link_memories=False)

        assert config.auto_link_memories == False

    def test_all_automation_enabled(self):
        """Test all automation enabled configuration."""
        config = AutomationConfig(
            auto_spill_messages=True,
            spill_threshold_bytes=8000,
            auto_distill=True,
            distill_trigger="message_count",
            distill_threshold=15,
            auto_store_memories=True,
            auto_link_memories=True
        )

        assert config.auto_spill_messages == True
        assert config.auto_distill == True
        assert config.auto_store_memories == True

    def test_all_automation_disabled(self):
        """Test all automation disabled configuration."""
        config = AutomationConfig(
            auto_spill_messages=False,
            auto_distill=False,
            auto_store_memories=False,
            auto_link_memories=False
        )

        assert config.auto_spill_messages == False
        assert config.auto_distill == False
        assert config.auto_store_memories == False
        assert config.auto_link_memories == False


class TestRetrievalStrategyEnum:
    """Test RetrievalStrategy enum."""

    def test_retrieval_strategy_values(self):
        """Test RetrievalStrategy enum values."""
        assert RetrievalStrategy.RECENT_FIRST.value == "recent_first"
        assert RetrievalStrategy.SEMANTIC_SIMILARITY.value == "semantic_similarity"
        assert RetrievalStrategy.HYBRID.value == "hybrid"

    def test_retrieval_strategy_use_in_config(self):
        """Test RetrievalStrategy enum usage in ContextConfig."""
        for strategy in RetrievalStrategy:
            config = ContextConfig(retrieval_strategy=strategy)
            assert config.retrieval_strategy == strategy