"""Tests for app/agent.py functions.

These tests cover validation, routing, and graph structure without
requiring LLM calls. Integration tests with actual models are handled
separately in notebooks/evaluation.
"""

import pytest

from app.agent import (
    AgentState,
    validate_query,
    check_validation,
    should_retry,
    make_schema_filter,
)
from app.config import MAX_RETRIES


def make_state(**kwargs) -> AgentState:
    """Create an AgentState with defaults for testing."""
    defaults = {
        "question": "List all artists",
        "relevant_tables": [],
        "schema_text": "",
        "raw_sql": "",
        "generated_sql": "",
        "is_valid": False,
        "validation_error": "",
        "results": None,
        "error": "",
        "retry_count": 0,
        "model_name": "test-model",
    }
    defaults.update(kwargs)
    return defaults


class TestValidateQuery:
    """Tests for validate_query() node."""

    def test_valid_select_query(self):
        state = make_state(generated_sql="SELECT * FROM Artist")
        result = validate_query(state)
        assert result["is_valid"] is True
        assert result["validation_error"] == ""

    def test_valid_query_with_join(self):
        state = make_state(
            generated_sql="SELECT a.Name, b.Title FROM Artist a JOIN Album b ON a.ArtistId = b.ArtistId"
        )
        result = validate_query(state)
        assert result["is_valid"] is True

    def test_empty_sql_invalid(self):
        state = make_state(generated_sql="")
        result = validate_query(state)
        assert result["is_valid"] is False
        assert "empty" in result["validation_error"].lower()

    def test_whitespace_only_invalid(self):
        state = make_state(generated_sql="   \n\t  ")
        result = validate_query(state)
        assert result["is_valid"] is False

    def test_blocks_insert(self):
        state = make_state(generated_sql="INSERT INTO Artist (Name) VALUES ('Test')")
        result = validate_query(state)
        assert result["is_valid"] is False
        assert "INSERT" in result["validation_error"]

    def test_blocks_update(self):
        state = make_state(generated_sql="UPDATE Artist SET Name = 'Test' WHERE ArtistId = 1")
        result = validate_query(state)
        assert result["is_valid"] is False
        assert "UPDATE" in result["validation_error"]

    def test_blocks_delete(self):
        state = make_state(generated_sql="DELETE FROM Artist WHERE ArtistId = 1")
        result = validate_query(state)
        assert result["is_valid"] is False
        assert "DELETE" in result["validation_error"]

    def test_blocks_drop(self):
        state = make_state(generated_sql="DROP TABLE Artist")
        result = validate_query(state)
        assert result["is_valid"] is False
        assert "DROP" in result["validation_error"]

    def test_invalid_syntax(self):
        # Use an unclosed parenthesis which sqlglot will reject
        state = make_state(generated_sql="SELECT * FROM Artist WHERE (Name = 'Test'")
        result = validate_query(state)
        assert result["is_valid"] is False


class TestCheckValidation:
    """Tests for check_validation() routing function."""

    def test_routes_to_execute_when_valid(self):
        state = make_state(is_valid=True, retry_count=0)
        assert check_validation(state) == "execute_query"

    def test_routes_to_error_when_invalid_and_retries_left(self):
        state = make_state(is_valid=False, retry_count=0)
        assert check_validation(state) == "handle_error"

    def test_routes_to_end_when_max_retries_reached(self):
        state = make_state(is_valid=False, retry_count=MAX_RETRIES)
        result = check_validation(state)
        assert result == "__end__"  # langgraph.graph.END


class TestShouldRetry:
    """Tests for should_retry() routing function."""

    def test_routes_to_error_on_execution_failure(self):
        state = make_state(error="no such table: Artistt", retry_count=1)
        assert should_retry(state) == "handle_error"

    def test_routes_to_end_on_success(self):
        state = make_state(error="", retry_count=0)
        result = should_retry(state)
        assert result == "__end__"

    def test_routes_to_end_when_max_retries_reached(self):
        state = make_state(error="some error", retry_count=MAX_RETRIES)
        result = should_retry(state)
        assert result == "__end__"


class TestSchemaFilter:
    """Tests for schema_filter node."""

    def test_selects_relevant_tables(self, test_schema_info):
        sample_rows = {}
        schema_filter = make_schema_filter(test_schema_info, sample_rows)

        state = make_state(question="Show me all artists")
        result = schema_filter(state)

        assert "Artist" in result["relevant_tables"]

    def test_includes_fk_related_tables(self, test_schema_info):
        sample_rows = {}
        schema_filter = make_schema_filter(test_schema_info, sample_rows)

        state = make_state(question="List all albums")
        result = schema_filter(state)

        # Album selected directly, Artist added via FK
        assert "Album" in result["relevant_tables"]
        assert "Artist" in result["relevant_tables"]

    def test_builds_schema_text(self, test_schema_info):
        sample_rows = {}
        schema_filter = make_schema_filter(test_schema_info, sample_rows)

        state = make_state(question="Show artists")
        result = schema_filter(state)

        assert "CREATE TABLE" in result["schema_text"]


class TestAgentImport:
    """Test that build_agent can be imported (basic sanity check)."""

    def test_build_agent_importable(self):
        from app.agent import build_agent
        assert callable(build_agent)


class TestAblationPrompts:
    """Tests for ablation study prompt selection (EXP-002).

    These tests verify the get_ablation_prompt function correctly returns
    the appropriate prompt template based on the ablation experiment type.
    """

    def test_zero_shot_returns_generic_prompt(self):
        from app.config import (
            get_ablation_prompt,
            PROMPT_ZERO_SHOT,
            GENERIC_PROMPT,
        )
        result = get_ablation_prompt(PROMPT_ZERO_SHOT)
        assert result == GENERIC_PROMPT

    def test_few_shot_returns_few_shot_prompt(self):
        from app.config import (
            get_ablation_prompt,
            PROMPT_FEW_SHOT,
            FEW_SHOT_PROMPT,
        )
        result = get_ablation_prompt(PROMPT_FEW_SHOT)
        assert result == FEW_SHOT_PROMPT
        assert "Example 1:" in result
        assert "Example 2:" in result

    def test_cot_returns_cot_prompt(self):
        from app.config import (
            get_ablation_prompt,
            PROMPT_COT,
            COT_PROMPT,
        )
        result = get_ablation_prompt(PROMPT_COT)
        assert result == COT_PROMPT
        assert "Reasoning:" in result
        assert "Tables needed:" in result

    def test_sqlcoder_overrides_ablation_type(self):
        from app.config import (
            get_ablation_prompt,
            PROMPT_FEW_SHOT,
            SQLCODER_PROMPT,
        )
        # sqlcoder should always use its specific prompt format
        result = get_ablation_prompt(PROMPT_FEW_SHOT, model_name="sqlcoder:7b")
        assert result == SQLCODER_PROMPT
