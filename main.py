"""
main.py
-------
Entry point for the project. Run this file to execute the full analysis:

    python main.py

WHY structure the project this way (main.py + src/ modules)?
Keeping each concern (loading the network, running the power flow,
plotting, the solar stretch feature) in its own file makes the project
easy to navigate and easy to explain: "main.py is just the recipe that
calls the steps in order; each step lives in its own file in src/".
This is a small-scale version of how real engineering codebases are
organized, which is a good thing to be able to point to in an interview.
"""

import copy
import os

from src.network_setup import load_ieee9_network, print_network_summary
from src.power_flow import run_power_flow, print_power_flow_report
from src.visualization import (
    plot_voltage_profile,
    plot_line_loading,
    plot_before_after_voltage,
    plot_before_after_losses,
)
from src.solar_integration import add_solar_generator, print_solar_comparison

OUTPUT_DIR = "outputs"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -----------------------------------------------------------------
    # STEP 1: Load the IEEE 9-bus test system
    # -----------------------------------------------------------------
    net = load_ieee9_network()
    print_network_summary(net)

    # -----------------------------------------------------------------
    # STEP 2: Run the base-case power flow (Newton-Raphson)
    # -----------------------------------------------------------------
    net = run_power_flow(net)
    print_power_flow_report(net, title="BASE CASE POWER FLOW RESULTS")

    # We keep a deep copy of the base-case network (with its results)
    # BEFORE adding solar, so we have a clean "before" snapshot to compare
    # against later. A shallow copy would still point to the same
    # internal tables, which would get overwritten once we modify `net`.
    net_before_solar = copy.deepcopy(net)

    # -----------------------------------------------------------------
    # STEP 3: Generate base-case plots
    # -----------------------------------------------------------------
    plot_voltage_profile(net, os.path.join(OUTPUT_DIR, "voltage_profile.png"))
    plot_line_loading(net, os.path.join(OUTPUT_DIR, "line_loading.png"))

    # -----------------------------------------------------------------
    # STEP 4 (stretch feature): Add a solar PV plant and re-run
    # -----------------------------------------------------------------
    net = add_solar_generator(net)
    net = run_power_flow(net)
    print_power_flow_report(net, title="POWER FLOW RESULTS WITH SOLAR PV ADDED")

    print_solar_comparison(net_before_solar, net)

    plot_before_after_voltage(
        net_before_solar.res_bus["vm_pu"].values,
        net.res_bus["vm_pu"].values,
        os.path.join(OUTPUT_DIR, "voltage_comparison_solar.png"),
    )
    loss_before = net_before_solar.res_line["pl_mw"].sum()
    loss_after = net.res_line["pl_mw"].sum()
    plot_before_after_losses(
        loss_before, loss_after,
        os.path.join(OUTPUT_DIR, "losses_comparison_solar.png"),
    )

    print("=" * 60)
    print(f"Done. All plots saved in the '{OUTPUT_DIR}/' folder.")
    print("=" * 60)


if __name__ == "__main__":
    main()
