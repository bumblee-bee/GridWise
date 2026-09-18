from typing import Any


SUPPORTED_DIRECTIVES = {
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
}


def validate_interpretation(result: dict, note_count: int) -> dict:
    if not isinstance(result, dict):
        raise ValueError("LLM output must be an object")

    items = result.get("directive_interpretation")

    if not isinstance(items, list):
        raise ValueError("directive_interpretation must be a list")

    if len(items) != note_count:
        raise ValueError(
            "LLM must return exactly one interpretation per note"
        )

    validated = []

    for expected_index, item in enumerate(items):

        if not isinstance(item, dict):
            raise ValueError("Each interpretation must be an object")

        note_index = item.get("note_index")
        directive_type = item.get("directive_type")
        applies = item.get("applies")
        adjustment = item.get("structured_adjustment")

        if note_index != expected_index:
            raise ValueError("note_index order is invalid")

        if directive_type not in SUPPORTED_DIRECTIVES:
            raise ValueError(
                f"Unsupported directive type: {directive_type}"
            )

        if directive_type == "no_op":
            if applies is not False:
                raise ValueError("no_op must have applies=false")

            if adjustment is not None:
                raise ValueError(
                    "no_op must have structured_adjustment=null"
                )

        else:
            if applies is not True:
                raise ValueError(
                    f"{directive_type} must have applies=true"
                )

            if not isinstance(adjustment, dict):
                raise ValueError(
                    f"{directive_type} requires structured_adjustment"
                )

            _validate_hours(adjustment.get("hours"))

            if directive_type == "solar_reduction":
                factor = adjustment.get("factor")

                if not isinstance(factor, (int, float)):
                    raise ValueError("solar factor must be numeric")

                if factor < 0 or factor > 1:
                    raise ValueError(
                        "solar factor must be between 0 and 1"
                    )

            elif directive_type == "minimum_battery_reserve":
                minimum = adjustment.get("minimum_energy_kwh")

                if not isinstance(minimum, (int, float)):
                    raise ValueError(
                        "minimum battery reserve must be numeric"
                    )

                if minimum < 0:
                    raise ValueError(
                        "minimum battery reserve cannot be negative"
                    )

            elif directive_type == "max_grid_window":
                maximum = adjustment.get("max_grid_kwh")

                if not isinstance(maximum, (int, float)):
                    raise ValueError(
                        "max_grid_kwh must be numeric"
                    )

                if maximum < 0:
                    raise ValueError(
                        "max_grid_kwh cannot be negative"
                    )

        validated.append(
            {
                "note_index": note_index,
                "directive_type": directive_type,
                "applies": applies,
                "structured_adjustment": adjustment,
            }
        )

    return {"directive_interpretation": validated}


def _validate_hours(hours: Any):
    if not isinstance(hours, list):
        raise ValueError("hours must be a list")

    if any(not isinstance(h, int) for h in hours):
        raise ValueError("directive hours must be integers")

    if any(h < 0 or h > 23 for h in hours):
        raise ValueError("directive hours must be between 0 and 23")

    if len(hours) != len(set(hours)):
        raise ValueError("directive hours must be unique")

    if hours != sorted(hours):
        raise ValueError("directive hours must be ascending")