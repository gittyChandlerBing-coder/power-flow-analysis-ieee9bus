"""
solar_integration.py
---------------------
Stretch feature: adds a solar photovoltaic plant to the network as a
"static generator" (sgen) and re-runs the power flow, so we can compare
the grid's behaviour before and after.

WHY model solar as an "sgen" instead of a "gen"?
In pandapower (and in the industry), a distinction is made between:
  - `gen`  : a conventional generator (like a coal/gas/hydro plant) that
             actively regulates its own voltage by adjusting reactive
             power output (a "PV bus" in load-flow terms).
  - `sgen` : a "static generator" -- used for inverter-based sources like
             solar PV, wind, or batteries, which typically just inject a
             fixed amount of real power (MW) at a given power factor and
             do NOT actively hold a voltage setpoint the way a big
             synchronous generator does. This is a more realistic model
             of how a solar farm actually behaves on the grid.

WHY bus 9 (index 8) and WHY 30 MW?
Bus 9 is the bus with the LOWEST voltage (0.958 pu) and the LARGEST load
(125 MW) in the base case -- so it's the most realistic candidate for
"where would a utility want extra local generation to help voltage
support and reduce losses". 30 MW represents a moderate-sized solar farm:
large enough to visibly change the results, but well below the 125 MW
local load, so the network stays realistic (we are not exporting power
back through the grid).
"""

import pandapower as pp

SOLAR_BUS_INDEX = 8       # Bus 9 (0-indexed) -- lowest voltage, highest load bus.
SOLAR_CAPACITY_MW = 30    # A moderate-sized solar PV plant.


def add_solar_generator(net, bus_index=SOLAR_BUS_INDEX, p_mw=SOLAR_CAPACITY_MW):
    """
    Adds a solar PV static generator to the network at the given bus.

    We set q_mvar=0 because solar inverters are commonly operated at (or
    very close to) unity power factor -- i.e. they supply real power (MW)
    only and neither consume nor supply reactive power, unless the plant
    is specifically configured to provide grid support.
    """
    pp.create_sgen(
        net,
        bus=bus_index,
        p_mw=p_mw,
        q_mvar=0,
        name="Solar PV Plant",
    )
    return net


def print_solar_comparison(net_before, net_after):
    """
    Prints a short before/after comparison table for voltages and losses,
    to make the impact of the solar plant obvious without re-reading two
    full reports.
    """
    print("=" * 60)
    print("BEFORE vs AFTER: Solar Generator Injection")
    print(f"(30 MW solar PV added at Bus {SOLAR_BUS_INDEX + 1})")
    print("=" * 60)

    v_before = net_before.res_bus["vm_pu"]
    v_after = net_after.res_bus["vm_pu"]

    print("\n--- Voltage magnitude (pu) ---")
    print(f"{'Bus':<8}{'Before':>10}{'After':>10}{'Change':>12}")
    for i in range(len(v_before)):
        change = v_after[i] - v_before[i]
        print(f"Bus {i + 1:<4}{v_before[i]:>10.4f}{v_after[i]:>10.4f}{change:>+12.4f}")

    loss_before = net_before.res_line["pl_mw"].sum()
    loss_after = net_after.res_line["pl_mw"].sum()
    print("\n--- Total real power loss (MW) ---")
    print(f"Before: {loss_before:.3f} MW")
    print(f"After : {loss_after:.3f} MW")
    print(f"Change: {loss_after - loss_before:+.3f} MW "
          f"({(loss_after - loss_before) / loss_before * 100:+.1f}%)")
    print()
