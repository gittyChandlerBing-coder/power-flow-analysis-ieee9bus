"""
visualization.py
-----------------
Turns the numeric results into simple bar charts.

WHY bar charts specifically (instead of, say, a line plot)?
Bus voltages and line loadings are values at DISCRETE, unordered points
(bus 1, bus 2, ... / line 1, line 2, ...) -- there's no continuous "x-axis"
between them. Bar charts are the standard, clearest way to compare
discrete categories against a reference line (like a voltage limit),
which is exactly what we need here.
"""

import matplotlib.pyplot as plt

from src.power_flow import VOLTAGE_LOWER_LIMIT_PU, VOLTAGE_UPPER_LIMIT_PU


def plot_voltage_profile(net, save_path):
    """
    Bar chart of voltage magnitude (pu) at every bus, with the 0.95-1.05 pu
    safe band drawn as reference lines.
    """
    voltages = net.res_bus["vm_pu"].values
    bus_labels = [f"Bus {i + 1}" for i in range(len(voltages))]

    # Color bars red if they violate the limits, green if they're fine.
    # WHY color-code? In an interview or a report, a reviewer should be
    # able to spot a problem bus in under a second, without reading numbers.
    colors = [
        "tomato" if (v < VOLTAGE_LOWER_LIMIT_PU or v > VOLTAGE_UPPER_LIMIT_PU) else "seagreen"
        for v in voltages
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(bus_labels, voltages, color=colors, edgecolor="black")

    # Reference lines for the safe operating band.
    ax.axhline(VOLTAGE_UPPER_LIMIT_PU, color="black", linestyle="--", linewidth=1,
               label=f"Upper limit ({VOLTAGE_UPPER_LIMIT_PU} pu)")
    ax.axhline(VOLTAGE_LOWER_LIMIT_PU, color="black", linestyle=":", linewidth=1,
               label=f"Lower limit ({VOLTAGE_LOWER_LIMIT_PU} pu)")
    ax.axhline(1.0, color="grey", linewidth=0.8)

    ax.set_ylim(0.9, 1.1)
    ax.set_ylabel("Voltage magnitude (per unit)")
    ax.set_title("Bus Voltage Profile - IEEE 9-Bus System")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {save_path}")


def plot_line_loading(net, save_path):
    """
    Bar chart of line loading percentage for every transmission line, with
    the 100% thermal limit drawn as a reference line.
    """
    loadings = net.res_line["loading_percent"].values
    line_labels = [
        f"L{f + 1}-{t + 1}"
        for f, t in zip(net.line["from_bus"], net.line["to_bus"])
    ]

    colors = ["tomato" if l > 100 else "steelblue" for l in loadings]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(line_labels, loadings, color=colors, edgecolor="black")
    ax.axhline(100, color="black", linestyle="--", linewidth=1, label="Thermal limit (100%)")

    ax.set_ylabel("Line loading (%)")
    ax.set_title("Transmission Line Loading - IEEE 9-Bus System")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {save_path}")


def plot_before_after_voltage(voltages_before, voltages_after, save_path):
    """
    Grouped bar chart comparing bus voltages before vs. after adding the
    solar generator (static generator / sgen).

    WHY a grouped (side-by-side) bar chart for the comparison?
    It's the clearest way to show "the same thing, measured twice" --
    each bus gets two adjacent bars, so the before/after difference at
    every single bus is visible at a glance.
    """
    bus_labels = [f"Bus {i + 1}" for i in range(len(voltages_before))]
    x = range(len(bus_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([i - width / 2 for i in x], voltages_before, width,
           label="Before solar", color="steelblue", edgecolor="black")
    ax.bar([i + width / 2 for i in x], voltages_after, width,
           label="After solar", color="orange", edgecolor="black")

    ax.axhline(1.0, color="grey", linewidth=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(bus_labels)
    ax.set_ylim(0.9, 1.1)
    ax.set_ylabel("Voltage magnitude (per unit)")
    ax.set_title("Voltage Profile: Before vs. After Solar Generator Injection")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {save_path}")


def plot_before_after_losses(losses_before, losses_after, save_path):
    """
    Simple bar chart comparing total real power (MW) losses before vs.
    after adding the solar generator.
    """
    labels = ["Before solar", "After solar"]
    values = [losses_before, losses_after]
    colors = ["steelblue", "orange"]

    fig, ax = plt.subplots(figsize=(5, 5))
    bars = ax.bar(labels, values, color=colors, edgecolor="black")

    # Label each bar with its exact value -- useful when the difference is
    # visually small but still worth pointing out in an interview.
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{value:.2f} MW", ha="center", va="bottom")

    ax.set_ylabel("Total real power loss (MW)")
    ax.set_title("System Losses: Before vs. After Solar Generator Injection")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {save_path}")
