def validate_plan(hours, battery, plan):
    if len(plan) != 24:
        raise ValueError("hourly_plan must contain exactly 24 hours")

    if [x["hour"] for x in plan] != list(range(24)):
        raise ValueError("hourly_plan hours must be exactly 0 to 23")

    energy = battery.initial_energy_kwh

    for source, item in zip(hours, plan):

        h = item["hour"]

        grid = float(item["grid_kwh"])
        solar = float(item["solar_used_kwh"])
        battery_kwh = float(item["battery_kwh"])
        after = float(item["battery_energy_after_kwh"])

        if grid < -0.01:
            raise ValueError(f"Negative grid at hour {h}")

        if solar < -0.01:
            raise ValueError(f"Negative solar at hour {h}")

        if solar > source.solar_kwh + 0.01:
            raise ValueError(f"Solar exceeds available solar at hour {h}")

        action = item["battery_action"]

        if action not in {"charge", "discharge", "idle"}:
            raise ValueError(f"Invalid battery action at hour {h}")

        if action == "charge":
            expected_after = energy + battery_kwh

            if battery_kwh < -0.01:
                raise ValueError(f"Invalid charge at hour {h}")

            if battery_kwh > battery.max_charge_kwh_per_hour + 0.01:
                raise ValueError(f"Charge limit exceeded at hour {h}")

        elif action == "discharge":
            expected_after = energy - battery_kwh

            if battery_kwh < -0.01:
                raise ValueError(f"Invalid discharge at hour {h}")

            if battery_kwh > battery.max_discharge_kwh_per_hour + 0.01:
                raise ValueError(f"Discharge limit exceeded at hour {h}")

        else:
            if abs(battery_kwh) > 0.01:
                raise ValueError(f"Idle hour has battery movement at hour {h}")

            expected_after = energy

        if abs(after - expected_after) > 0.01:
            raise ValueError(
                f"Battery energy transition invalid at hour {h}"
            )

        if after < battery.minimum_energy_kwh - 0.01:
            raise ValueError(f"Battery below minimum at hour {h}")

        if after > battery.capacity_kwh + 0.01:
            raise ValueError(f"Battery exceeds capacity at hour {h}")

        expected_demand = (
            grid
            + solar
            + (
                battery_kwh
                if action == "discharge"
                else 0
            )
        )

        supplied_demand = (
            source.demand_kwh
            + (
                battery_kwh
                if action == "charge"
                else 0
            )
        )

        if abs(expected_demand - supplied_demand) > 0.01:
            raise ValueError(
                f"Energy balance invalid at hour {h}"
            )

        energy = after

    if abs(
        energy - battery.initial_energy_kwh
    ) > 0.01:
        raise ValueError(
            "End-of-day battery energy must equal initial energy"
        )

    return True