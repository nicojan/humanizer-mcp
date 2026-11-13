"""humanizer_check_text — deterministic compliance checker tool.

Read-only with respect to server state (analyzes input, mutates nothing).
Does NOT log the input text."""

import json
from typing import Literal, Optional

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
            "Optional content type: 'academic', 'marketing', 'tech'/'technical', "
            "or 'prose' (default). Pass 'label' or 'notes' for headings, "
            "worksheet cells, UI strings or CEFR-pitched copy: sentence-length "
            "numbers are still reported and segment_uniformity is not reported "
            "as a finding, and every other layer runs. "
            "Pass 'resume' (or 'cv') for a résumé: the same, and rule-of-three "
            "density is also skipped, because a Skills block is a list. "
            "'case_study' (or 'portfolio') runs as prose; its guidance is in "
            "humanizer_get_content_profile. The report's manual_review is "
            "filtered by content_type; with none, every rubric item is sent."
        ),
    )
    rubric: Optional[Literal["short", "full"]] = Field(
        default="short",
        description=(
            "Which self-review rubric the report's manual_review carries. "
            "'short' (default) sends one line per item for the content_type, "
            "for every iteration of the write-check-fix loop. 'full' sends each "
            "item's complete text; use it once, on the last check of the "
            "assembled document, and do the self-review against your draft."
        ),
    )


def check_text_handler(text: str, content_type: Optional[str], rubric: str = "short") -> str:
    report = run_checks(text, content_type, rubric or "short")
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
        server cannot perform (short lines by default, the full rubric with
        rubric="full"). Re-run after fixing until prohibitions_clear, then make
        one last call on the assembled document with rubric="full".

        Args:
            params: CheckTextInput with text (required), optional content_type
                and optional rubric ("short" or "full").

        Returns:
            str: Compact JSON compliance report.
        """
        return check_text_handler(params.text, params.content_type, params.rubric or "short")
