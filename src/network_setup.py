"""
network_setup.py
-----------------
This file is responsible for ONE thing only: getting us a ready-to-use
electrical network model to run a power flow on.

WHY a separate file for this?
In real projects, "build/load the model" and "analyze the model" are kept
separate. It makes the code easier to read, easier to test, and easier to
explain: anyone opening this file immediately knows "this is where the
network comes from", without wading through power flow math.
"""

import pandapower as pp
import pandapower.networks as pn


def load_ieee9_network():
    """
    Loads the IEEE 9-bus test system (also known as the WSCC 9-bus system).

    WHY this test case?
    - It's one of the oldest and most widely taught power system models
      (from Anderson & Fouad's textbook), so interviewers are likely to
      recognize it immediately.
    - It's small (9 buses, 3 generators, 3 loads), so results are easy to
      reason about by hand -- good for explaining in an interview.
    - pandapower ships it as a ready-made, well-tested built-in network
      (pandapower.networks.case9), so we don't need to manually enter bus
      and line data ourselves, which is where most beginner mistakes happen.

    Returns
    -------
    net : pandapowerNet
        A pandapower network object. Think of this as an in-memory
        spreadsheet of tables (buses, lines, loads, generators, etc.)
        that pandapower knows how to solve a power flow on.
    """
    net = pn.case9()

    # A quick sanity check so we fail loudly (and early) if the network
    # didn't load the way we expect, instead of getting confusing errors
    # later during the power flow step.
    assert len(net.bus) == 9, "Expected the IEEE 9-bus system to have 9 buses."

    return net


def print_network_summary(net):
    """
    Prints a short, human-readable summary of the network so we can sanity
    check what we're about to analyze before running any calculations.

    WHY print this at all?
    In an interview, being able to say "the network has 9 buses, 3
    generators, 3 loads, and 9 transmission lines, all at 345 kV" shows you
    actually understand the system you're analyzing -- not just that you
    ran a library function.
    """
    print("=" * 60)
    print("NETWORK SUMMARY: IEEE 9-Bus (WSCC) Test System")
    print("=" * 60)
    print(f"Buses (nodes)         : {len(net.bus)}")
    print(f"Transmission lines    : {len(net.line)}")
    print(f"Generators (PV buses) : {len(net.gen)}")
    print(f"External grid (slack) : {len(net.ext_grid)}")
    print(f"Loads (demand points) : {len(net.load)}")
    print(f"Voltage level         : {net.bus['vn_kv'].unique()[0]} kV")
    print()
