from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.schemas import OptimizeRequest
from app.llm import interpret_operator_notes
from app.guardrails import validate_interpretation
from app.optimizer import optimize_energy
from app.validator import validate_plan


load_dotenv()

app = FastAPI(
    title="GridWise Energy Optimization API",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/optimize-energy")
def optimize_energy_endpoint(
    request: OptimizeRequest
):
    try:

        # -------------------------------------------------
        # STEP 1: LLM interprets operator notes
        # -------------------------------------------------
        raw_interpretation = interpret_operator_notes(
            request.operator_notes
        )

        # -------------------------------------------------
        # STEP 2: Validate LLM output
        # -------------------------------------------------
        validated_interpretation = validate_interpretation(
            raw_interpretation,
            len(request.operator_notes)
        )

        # -------------------------------------------------
        # STEP 3: Optimize energy
        # -------------------------------------------------
        optimization = optimize_energy(
            request.hours,
            request.battery,
            validated_interpretation[
                "directive_interpretation"
            ]
        )

        # -------------------------------------------------
        # STEP 4: Validate final 24-hour plan
        # -------------------------------------------------
        validate_plan(
            request.hours,
            request.battery,
            optimization["hourly_plan"]
        )

        # -------------------------------------------------
        # STEP 5: Return final response
        # -------------------------------------------------
        return {
            "scenario_id": request.scenario_id,

            "directive_interpretation":
                validated_interpretation[
                    "directive_interpretation"
                ],

            "hourly_plan":
                optimization["hourly_plan"],

            "total_grid_kwh":
                optimization["total_grid_kwh"],

            "total_cost_bdt":
                optimization["total_cost_bdt"],

            "peak_grid_kwh":
                optimization["peak_grid_kwh"],

            "plan_summary":
                "Energy schedule optimized using "
                "validated operator directives."
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )