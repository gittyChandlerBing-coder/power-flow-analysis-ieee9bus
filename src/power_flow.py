"""
power_flow.py
-------------
This file runs the actual power flow (a.k.a. "load flow") calculation and
pulls out the numbers we care about.

WHAT is a power flow / load flow analysis? (in plain English)
Every generator produces power, and every load consumes power, but the
voltage at each bus and the current flowing through each line are NOT
things we can just set directly -- they depend on how the whole network is
wired together (like water pressure in connected pipes). A power flow
study solves this "what happens everywhere, given these generators and
loads" problem. It's the single most-run calculation in the power industry
-- grid operators run it constantly to make sure the grid will stay stable
and within safe voltage limits.

WHY Newton-Raphson specifically?
Newton-Raphson is an iterative numerical method: it starts with a guess for
all bus voltages, checks how wrong that guess is (the "mismatch" between
power flowing in vs. required), and then uses calculus (the Jacobian
matrix of partial derivatives) to make a smarter guess. It repeats this
until the mismatch is smaller than a tolerance (pandapower defaults to a
very small number). It's the industry-standard method because it
converges in very few iterations (usually 3-5) even for large, realistic
grids, which matters a lot when you're solving this thousands of times a
day for a real grid.
"""

import pandapower as pp


# Standard voltage band used across the power industry for a "healthy" bus.
# Anything outside this range is normally flagged for operator attention.
VOLTAGE_LOWER_LIMIT_PU = 0.95
VOLTAGE_UPPER_LIMIT_PU = 1.05


def run_power_flow(net):
    """
    Runs an AC power flow on the given network using the Newton-Raphson
    method.

    WHY explicitly pass algorithm="nr"?
    pandapower's default is already Newton-Raphson, but we set it
    explicitly so the code is self-documenting -- anyone reading this line
    immediately knows which numerical method solved the network, without
    needing to check pandapower's defaults.

    WHY numba=False?
    pandapower can optionally use the "numba" library to just-in-time
    compile parts of the solver for extra speed on large networks
    (hundreds/thousands of buses). For a 9-bus system this makes no
    noticeable difference, and skipping it avoids an extra ~150 MB
    dependency and a compile step -- a sensible trade-off on a modest
    4 GB RAM machine.
    """
    pp.runpp(net, algorithm="nr", numba=False)

    if not net.converged:
        # A power flow can fail to converge if the grid is under extreme
        # stress (e.g. way too much load, or a badly configured network).
        # We raise an error here instead of silently continuing with
        # meaningless numbers.
        raise RuntimeError("Power flow did not converge. Check network data.")

    return net


def get_bus_voltage_results(net):
    """
    Returns a small, clean table of voltage magnitude (in per-unit) and
    angle for every bus.

    WHY per-unit (pu) instead of kV?
    Power systems use a "per-unit" system where 1.0 pu means "exactly the
    nominal/rated voltage for that bus". This lets us compare a 345 kV bus
    and an 11 kV bus on the same 0-to-1-ish scale, and instantly see if a
    voltage is high or low relative to what it *should* be, without doing
    unit conversions in our head.
    """
    results = net.res_bus[["vm_pu", "va_degree"]].copy()
    results.insert(0, "bus_name", net.bus["name"].values)
    results.columns = ["bus_name", "voltage_pu", "angle_degrees"]
    return results


def get_line_loading_results(net):
    """
    Returns a table of how "loaded" (i.e. how close to its thermal limit)
    each transmission line is, as a percentage.

    WHY does line loading % matter?
    Every line has a maximum safe current it can carry before it overheats
    and sags or gets damaged. "Loading percent" tells us, for each line,
    what fraction of that limit is currently being used. 100% loading means
    the line is at its rated limit; above 100% means it is overloaded.
    This is one of the first things a grid operator checks.
    """
    results = net.res_line[["loading_percent", "p_from_mw", "q_from_mvar"]].copy()
    results.insert(
        0,
        "line",
        [f"Line {f + 1}-{t + 1}" for f, t in zip(net.line["from_bus"], net.line["to_bus"])],
    )
    results.columns = ["line", "loading_percent", "p_from_mw", "q_from_mvar"]
    return results


def get_total_losses(net):
    """
    Returns total real (MW) and reactive (Mvar) power losses across all
    transmission lines.

    WHY do losses matter, and why can reactive losses be negative?
    Real power (MW) losses are pure waste -- energy that's lost as heat in
    the line's resistance, and utilities are financially penalized for
    this, so minimizing it is a real economic concern.

    Reactive power (Mvar) is different: it doesn't do useful "work", but
    it's needed to maintain voltage levels. Long high-voltage lines have
    capacitance between the conductors and ground, which actually GENERATES
    reactive power when the line is lightly loaded. So a negative reactive
    "loss" isn't a mistake -- it means the line is a net producer of
    reactive power at this loading level, which is completely normal for
    lightly-loaded EHV (extra-high-voltage) transmission lines like the
    345 kV lines in this system.
    """
    total_p_loss_mw = net.res_line["pl_mw"].sum()
    total_q_loss_mvar = net.res_line["ql_mvar"].sum()
    return total_p_loss_mw, total_q_loss_mvar


def get_voltage_violations(net):
    """
    Returns a table of any buses whose voltage falls outside the standard
    0.95 - 1.05 pu safe operating band.

    WHY this specific band?
    0.95-1.05 pu (i.e. +/- 5% of nominal voltage) is a very common
    industry rule-of-thumb operating limit. Equipment connected to the grid
    (transformers, motors, electronics) is designed to tolerate small
    voltage swings, but voltages outside this band can cause equipment
    damage, tripping/protection issues, or reduced power quality.
    """
    voltages = get_bus_voltage_results(net)
    violations = voltages[
        (voltages["voltage_pu"] < VOLTAGE_LOWER_LIMIT_PU)
        | (voltages["voltage_pu"] > VOLTAGE_UPPER_LIMIT_PU)
    ]
    return violations


def print_power_flow_report(net, title="POWER FLOW RESULTS"):
    """
    Prints a full, readable report of the power flow results to the
    console. This is the function main.py calls to show everything at
    once.
    """
    print("=" * 60)
    print(title)
    print("=" * 60)

    print("\n--- Bus Voltages (per unit) ---")
    print(get_bus_voltage_results(net).to_string(index=False))

    print("\n--- Line Loading (%) ---")
    print(get_line_loading_results(net)[["line", "loading_percent"]].to_string(index=False))

    p_loss, q_loss = get_total_losses(net)
    print("\n--- System Losses ---")
    print(f"Total real power loss     : {p_loss:.3f} MW")
    print(f"Total reactive power loss : {q_loss:.3f} Mvar")

    print("\n--- Voltage Violation Check (limits: 0.95 - 1.05 pu) ---")
    violations = get_voltage_violations(net)
    if violations.empty:
        print("No voltage violations. All buses are within 0.95-1.05 pu.")
    else:
        print(violations.to_string(index=False))
    print()
