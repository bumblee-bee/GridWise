import numpy as np
from scipy.optimize import linprog


def optimize_energy(hours, battery, interpretation):

    n = 24

    demand = np.array(
        [h.demand_kwh for h in hours],
        dtype=float
    )

    solar = np.array(
        [h.solar_kwh for h in hours],
        dtype=float
    )

    tariff = np.array(
        [h.tariff_bdt_per_kwh for h in hours],
        dtype=float
    )

    effective_solar = solar.copy()

    reserve = np.full(
        n,
        battery.minimum_energy_kwh,
        dtype=float
    )

    max_grid = np.full(
        n,
        np.inf,
        dtype=float
    )

    allow_charge = np.ones(n, dtype=bool)
    allow_discharge = np.ones(n, dtype=bool)

    # Apply validated directives
    for directive in interpretation:

        if not directive["applies"]:
            continue

        dtype = directive["directive_type"]
        adjustment = directive["structured_adjustment"]
        directive_hours = adjustment["hours"]

        if dtype == "solar_reduction":
            factor = float(adjustment["factor"])

            for h in directive_hours:
                effective_solar[h] *= factor

        elif dtype == "minimum_battery_reserve":
            minimum = float(
                adjustment["minimum_energy_kwh"]
            )

            for h in directive_hours:
                reserve[h] = max(reserve[h], minimum)

        elif dtype == "no_charge_window":

            for h in directive_hours:
                allow_charge[h] = False

        elif dtype == "no_discharge_window":

            for h in directive_hours:
                allow_discharge[h] = False

        elif dtype == "max_grid_window":
            maximum = float(
                adjustment["max_grid_kwh"]
            )

            for h in directive_hours:
                max_grid[h] = min(max_grid[h], maximum)

    # Variable layout per hour:
    # grid, solar_used, charge, discharge, battery_energy
    def idx(h, variable):
        return h * 5 + variable

    GRID = 0
    SOLAR = 1
    CHARGE = 2
    DISCHARGE = 3
    ENERGY = 4

    total_variables = n * 5

    objective = np.zeros(total_variables)

    for h in range(n):
        objective[idx(h, GRID)] = tariff[h]

        # Tiny throughput penalty discourages unnecessary
        # charge/discharge cycling.
        objective[idx(h, CHARGE)] = 1e-7
        objective[idx(h, DISCHARGE)] = 1e-7

    bounds = []

    for h in range(n):

        # Grid
        grid_upper = max_grid[h]

        bounds.append(
            (0, grid_upper)
        )

        # Solar used
        bounds.append(
            (0, effective_solar[h])
        )

        # Charge
        charge_upper = (
            battery.max_charge_kwh_per_hour
            if allow_charge[h]
            else 0
        )

        bounds.append(
            (0, charge_upper)
        )

        # Discharge
        discharge_upper = (
            battery.max_discharge_kwh_per_hour
            if allow_discharge[h]
            else 0
        )

        bounds.append(
            (0, discharge_upper)
        )

        # Battery energy
        bounds.append(
            (
                reserve[h],
                battery.capacity_kwh
            )
        )

    equality_matrix = []
    equality_values = []

    for h in range(n):

        # grid + solar + discharge
        # = demand + charge
        row = np.zeros(total_variables)

        row[idx(h, GRID)] = 1
        row[idx(h, SOLAR)] = 1
        row[idx(h, DISCHARGE)] = 1
        row[idx(h, CHARGE)] = -1

        equality_matrix.append(row)
        equality_values.append(demand[h])

        # Battery energy transition
        row = np.zeros(total_variables)

        row[idx(h, ENERGY)] = 1
        row[idx(h, CHARGE)] = -1
        row[idx(h, DISCHARGE)] = 1

        if h == 0:
            equality_values.append(
                battery.initial_energy_kwh
            )
        else:
            row[idx(h - 1, ENERGY)] = -1
            equality_values.append(0)

        equality_matrix.append(row)

    # End-of-day neutrality
    row = np.zeros(total_variables)
    row[idx(23, ENERGY)] = 1

    equality_matrix.append(row)
    equality_values.append(
        battery.initial_energy_kwh
    )

    result = linprog(
        objective,
        A_eq=np.array(equality_matrix),
        b_eq=np.array(equality_values),
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        raise ValueError(
            f"No valid energy schedule found: {result.message}"
        )

    plan = []

    for h in range(n):

        grid = result.x[idx(h, GRID)]
        solar_used = result.x[idx(h, SOLAR)]
        charge = result.x[idx(h, CHARGE)]
        discharge = result.x[idx(h, DISCHARGE)]
        energy = result.x[idx(h, ENERGY)]

        if charge > 1e-7:
            action = "charge"
            battery_kwh = charge
        elif discharge > 1e-7:
            action = "discharge"
            battery_kwh = discharge
        else:
            action = "idle"
            battery_kwh = 0.0

        plan.append(
            {
                "hour": h,
                "grid_kwh": round(float(grid), 6),
                "solar_used_kwh": round(float(solar_used), 6),
                "battery_action": action,
                "battery_kwh": round(float(battery_kwh), 6),
                "battery_energy_after_kwh": round(
                    float(energy), 6
                ),
            }
        )

    total_grid = sum(
        item["grid_kwh"] for item in plan
    )

    total_cost = sum(
        item["grid_kwh"] * tariff[item["hour"]]
        for item in plan
    )

    peak_grid = max(
        item["grid_kwh"] for item in plan
    )

    return {
        "hourly_plan": plan,
        "total_grid_kwh": round(total_grid, 6),
        "total_cost_bdt": round(float(total_cost), 6),
        "peak_grid_kwh": round(peak_grid, 6),
    }