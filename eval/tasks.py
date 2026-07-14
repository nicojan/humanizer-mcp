"""Tiny Step-1 benchmark. Genres reuse names from content_profiles.json so the
eval maps onto what the MCP serves. Expand toward ~20-30 in Step 2.

These are the prompts you run under each condition. The harness does NOT generate
text (no API): produce each output yourself (unaided, and with the rules applied)
and save them as eval/outputs/<condition>/<id>.txt for the harness to score."""

TASKS = [
    {
        "id": "cover_letter",
        "genre": "cover_letter",
        "prompt": "Write a 150-word cover letter for a junior marketing role at a "
        "small bakery. The applicant has retail experience but no marketing degree.",
    },
    {
        "id": "product_blurb",
        "genre": "marketing",
        "prompt": "Write a 120-word product description for a reusable stainless "
        "steel water bottle aimed at hikers.",
    },
    {
        "id": "howto_intro",
        "genre": "technical",
        "prompt": "Write a 150-word introduction to a tutorial on setting up a "
        "Python virtual environment, for a reader who has never used one.",
    },
    {
        "id": "personal_anecdote",
        "genre": "prose",
        "prompt": "Write a 150-word personal anecdote about the first time you "
        "cooked a meal for someone you wanted to impress.",
    },
]
