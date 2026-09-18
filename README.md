\# GridWise



\## LLM-Assisted Energy Optimization API



GridWise is a 24-hour campus energy optimization service developed for the BUP CSE Fest 2026 Hackathon: Smart Campus Energy Optimization Challenge.



The system interprets natural-language operator notes using a language-capable generative model, converts them into supported structured directives, validates the model output through deterministic guardrails, applies the resulting constraints, and generates a cost-optimized hourly energy schedule.



\## Solution Overview



GridWise follows the following processing pipeline:



Operator Notes

&#x20;   ->

LLM Directive Interpretation

&#x20;   ->

Deterministic Guardrails

&#x20;   ->

Directive Application

&#x20;   ->

24-Hour Energy Optimization

&#x20;   ->

Final Schedule Validation

&#x20;   ->

API Response



The language model is used specifically for interpreting `operator\_notes`. Deterministic validation and optimization are performed after the LLM interpretation.



\## Supported Operator Directives



The implementation supports the following directive types:



\- `solar\_reduction`

\- `minimum\_battery\_reserve`

\- `no\_charge\_window`

\- `no\_discharge\_window`

\- `max\_grid\_window`

\- `no\_op`



For each operator note, the system produces exactly one structured interpretation in note order.



`no\_op` is represented with:



```json

{

&#x20; "applies": false,

&#x20; "structured\_adjustment": null

}

