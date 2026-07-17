# Power Flow Analysis using pandapower on the IEEE 9-Bus System

A small, self-contained Python project that runs a Newton-Raphson power
flow (load flow) study on the classic IEEE 9-bus (WSCC) test system, then
adds a solar PV plant to show its impact on voltage and losses. Built to
be light enough to run on a modest laptop (4 GB RAM), and simple enough to
explain confidently in a placement interview.

---

## 1. What is "power flow analysis"? (in plain English)

A power grid is a network of generators, loads, and transmission lines all
connected together, a bit like a network of connected water pipes. If you
know how much power each generator is producing and each load is
consuming, you still don't automatically know the voltage at every point
in the network or how much current is flowing through every line -- that
depends on how everything is wired together. **Power flow (load flow)
analysis is the calculation that figures out exactly that**: the voltage
magnitude and angle at every bus, and the power flowing through every
line, for a given snapshot of generation and demand. It's the single most
frequently run calculation in the power industry -- grid operators run it
constantly to make sure the network stays within safe voltage and thermal
limits.

## 2. What this project does

1. Loads the **IEEE 9-bus test system** (also called the WSCC 9-bus
   system) using pandapower's built-in network library.
2. Runs an AC power flow using the **Newton-Raphson method**.
3. Extracts and prints:
   - Voltage magnitude at every bus (in per-unit)
   - Line loading percentage for every transmission line
   - Total real (MW) and reactive (Mvar) power losses
   - Any buses violating the standard 0.95-1.05 pu safe voltage band
4. Generates two plots: a bus voltage bar chart and a line loading bar
   chart, saved to `outputs/`.
5. **Stretch feature**: adds a 30 MW solar PV plant (modeled as a static
   generator) at Bus 9, re-runs the power flow, and produces two more
   plots comparing voltage profile and system losses before vs. after.

## 3. How to run it

```bash
# 1. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 2. Install the minimal dependencies
pip install -r requirements.txt
# (equivalent to: pip install pandapower pandas matplotlib)

# 3. Run the analysis
python main.py
```

That's it -- no GUI, no cloud services, no paid tools, no internet
connection needed once the packages are installed. It runs in a few
seconds on a low-end laptop.

**Output:**
- Full results are printed to the console.
- Four `.png` plots are saved to `outputs/`.
- A saved sample run is included at `results/sample_output.txt` so you can
  review the numbers without re-running the code.

## 4. Project structure

```
power_flow_analysis/
├── README.md
├── requirements.txt
├── main.py                        # Entry point -- runs everything in order
├── src/
│   ├── network_setup.py           # Loads the IEEE 9-bus network
│   ├── power_flow.py               # Runs Newton-Raphson power flow, extracts results
│   ├── visualization.py            # All matplotlib plotting functions
│   └── solar_integration.py        # Stretch feature: adds solar PV, before/after comparison
├── outputs/                        # Generated plots (created when you run main.py)
│   ├── voltage_profile.png
│   ├── line_loading.png
│   ├── voltage_comparison_solar.png
│   └── losses_comparison_solar.png
└── results/
    └── sample_output.txt           # A saved sample console run, for reference
```

## 5. What the results mean (plain English)

- **Voltage magnitude (pu)**: 1.0 pu means "exactly the voltage this bus
  is rated for". In this base case, all 9 buses sit between about 0.958
  and 1.003 pu -- comfortably inside the 0.95-1.05 pu band utilities
  treat as "healthy". No violations were found.
- **Line loading (%)**: how close each line is to its thermal (current)
  limit. The most heavily loaded line in this system runs around 65%,
  well under 100%, so there's no line at risk of overloading in this
  scenario.
- **Losses**: about 4.95 MW of real power is lost as heat across the
  whole network -- this is the "waste" a utility wants to minimize.
  Interestingly, the *reactive* power loss comes out **negative**
  (around -80 Mvar). That's not a bug: long, lightly-loaded high-voltage
  lines generate more reactive power (via their natural capacitance) than
  they consume, so a negative number here just means the lines are net
  reactive power *producers* at this loading level.
- **Solar PV addition**: adding a 30 MW solar plant at Bus 9 (the
  lowest-voltage, most heavily loaded bus) raised its voltage from 0.958
  to 0.961 pu and reduced total system losses from 4.96 MW to 4.75 MW
  (about 4% lower) -- because generating power closer to where it's
  consumed means less of it has to travel over lossy transmission lines.

## 6. Decisions made on your behalf (and why)

Since you said to pick sensible defaults rather than ask:

- **Test case: IEEE 9-bus (`pandapower.networks.case9`)**, not 14-bus.
  It's smaller (easier to explain bus-by-bus in an interview), it's one
  of the most widely taught systems in power system textbooks, and it
  loaded and converged cleanly with no extra configuration.
- **Solar plant location: Bus 9**, because it has the lowest voltage
  (0.958 pu) and the largest load (125 MW) in the base case -- the most
  realistic spot for a utility to consider adding local generation.
- **Solar capacity: 30 MW**, a moderate size relative to Bus 9's 125 MW
  load -- large enough to visibly move the numbers, small enough that the
  network stays realistic (no reverse power flow out of the local area).
- **Solar modeled as `sgen` (static generator), not `gen`**: this matches
  how inverter-based solar actually behaves on the grid (fixed real power
  injection at a given power factor), rather than actively regulating
  voltage the way a large synchronous generator does.
- **numba disabled** (`numba=False` in the power flow call): numba gives
  a solver speedup that only matters for much larger networks, and
  skipping it avoids installing an extra ~150 MB dependency -- a sensible
  trade-off given your 4 GB RAM machine.

## 7. Key Learnings / Interview Talking Points

- **"What is load flow analysis used for in real power systems?"** -- It's
  the core calculation grid operators use to check, before and during
  operation, that voltages stay within safe limits and no line gets
  overloaded, for any given combination of generation and demand. It's
  also the foundation other studies (contingency analysis, short-circuit
  studies, planning studies) build on top of.
- **"What does Newton-Raphson actually do?"** -- It's an iterative
  numerical method: start with a guess for every bus voltage, measure how
  far off the power balance is (the "mismatch"), use the Jacobian matrix
  (partial derivatives) to compute a better guess, and repeat until the
  mismatch is smaller than a tiny tolerance. It typically converges in
  just 3-5 iterations even on large networks, which is why it's the
  industry-standard method over slower alternatives like Gauss-Seidel.
- **"What does a voltage violation mean practically?"** -- If a bus
  voltage drops below 0.95 pu, connected equipment may not operate
  correctly and motors can stall or overheat; if it rises above 1.05 pu,
  insulation stress increases and equipment lifespan can be reduced. Grid
  operators treat this band as the line between "normal operation" and
  "needs corrective action" (like switching in capacitors or generation).
- **"Why does adding solar generation change losses and voltage?"** --
  Generating power physically closer to where it's consumed means less
  power has to travel over resistive transmission lines, which is why
  losses dropped and the local voltage improved when solar was added at
  the most heavily loaded bus.
- **"Why per-unit (pu) instead of raw kV or MW?"** -- Per-unit
  normalizes every quantity relative to its own rated value, so a 345 kV
  transmission bus and an 11 kV distribution bus can both be read on the
  same 0-to-1-ish scale -- this is standard practice across the power
  industry precisely because it makes results comparable at a glance.

---

*Built with [pandapower](https://www.pandapower.org/), an open-source
Python library for power system modeling and analysis.*
