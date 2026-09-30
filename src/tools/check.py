"""humanizer_check_text — deterministic compliance checker tool.

Read-only with respect to server state (analyzes input, mutates nothing).
Does NOT log the input text."""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from src.checker import run_checks


class CheckTextInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(
        min_length=1,
        max_length=100_000,
        description="The candidate text to check for humanization compliance.",
    )
    content_type: Optional[str] = Field(
        default=None,
        description=(
            "Optional content type tuning the burstiness target: 'academic', "
            "'marketing', 'tech'/'technical', or 'prose' (default). Pass "
            "'label' or 'notes' for headings, worksheet cells, UI strings or "
            "CEFR-pitched copy: burstiness and segment_uniformity are still "
            "measured but not reported as findings, and every other layer runs."
        ),
    )


def check_text_handler(text: str, content_type: Optional[str]) -> str:
    report = run_checks(text, content_type)
    return json.dumps(report, separators=(",", ":"), ensure_ascii=False)


def register_check_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="humanizer_check_text",
        annotations={
            "title": "Check Text for Humanization Compliance",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def humanizer_check_text(params: CheckTextInput) -> str:
        """Run deterministic humanization checks on candidate text and return a
        compliance report. prohibitions_clear is true only when no hard
        prohibitions (em-dashes, fixed AI phrases) remain. must_clear lists
        located findings to rewrite or justify; manual_review lists checks the
        server cannot perform. Re-run after fixing until prohibitions_clear.

        Args:
            params: CheckTextInput with text (required) and optional content_type.

        Returns:
            str: Compact JSON compliance report.
        """
        return check_text_handler(params.text, params.content_type)
