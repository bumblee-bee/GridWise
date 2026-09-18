import json
import os

from openai import OpenAI


SYSTEM_PROMPT = """
You are the GridWise operator-note interpreter.

Your job is ONLY to convert operator notes into one supported structured directive.

Supported directive types:
1. solar_reduction
2. minimum_battery_reserve
3. no_charge_window
4. no_discharge_window
5. max_grid_window
6. no_op

Rules:
- Return exactly one interpretation for each note.
- Preserve note_index.
- Hours must be unique integers from 0 to 23, ascending.
- Time windows are start-inclusive and end-exclusive.
- For solar_reduction, factor means the usable fraction remaining.
- Example: 80% reduction means factor 0.2.
- Do not invent values.
- If a note is unrelated to energy optimization, use no_op.
- Do not create unsupported directive types.

Return ONLY valid JSON:

{
  "directive_interpretation": [
    {
      "note_index": 0,
      "directive_type": "no_op",
      "applies": false,
      "structured_adjustment": null
    }
  ]
}
"""


def interpret_operator_notes(operator_notes):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    client = OpenAI(api_key=api_key)

    user_prompt = json.dumps(
        {
            "operator_notes": operator_notes
        },
        ensure_ascii=False
    )

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
    )

    return json.loads(response.output_text)