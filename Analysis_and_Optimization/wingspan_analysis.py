"""
wingspan_analysis.py

Sweeps the wing span and computes the mission score for each value.
All other design variables are taken from overall_inputs.DESIGN_VARIABLES_EXAMPLE.

Run from the repo root:
    python -m Analysis_and_Optimization.wingspan_analysis
"""

import matplotlib.pyplot as plt
import numpy as np

import overall_inputs
from Aerodynamics import aerodynamics
from Performance import mission_sim as msim
from Performance.score_calculation import calc_score
from Propulsion import propulsion
from Structure import structures


def wingspan_analysis(spans=None, base_design_variables=None, verbose=False):
    """Compute the score for every wing span in `spans`.

    Returns (spans, scores) as numpy arrays.
    """
    if spans is None:
        spans = np.round(np.arange(1.0, 2.0 + 1e-9, 0.1), 2)  # 1.0 ... 2.0 m
    if base_design_variables is None:
        base_design_variables = overall_inputs.DESIGN_VARIABLES_EXAMPLE

    scores = np.zeros(len(spans))
    for i, span in enumerate(spans):
        dv = dict(base_design_variables)  # copy, so the example is not modified
        dv["wing_span"] = float(span)

        t_mission, d_to = msim.mission_sim(dv)

        m = structures.aircraft_mass(dv)
        S = aerodynamics.wing_area(dv)
        v_stall = aerodynamics.stall_speed(m, S, aerodynamics.CL_max(dv))

        cost = propulsion.total_component_cost(dv)

        scores[i] = calc_score(t_mission, cost, v_stall, d_to)

        if verbose:
            print(
                f"b = {span:4.2f} m | T_mission = {t_mission:7.1f} s | "
                f"d_to = {d_to:5.1f} m | v_stall = {v_stall:4.1f} m/s | score = {scores[i]:.2f}"
            )

    return np.asarray(spans), scores


def plot_scores(spans, scores):
    """Plot score over wing span and mark the best span."""
    i_best = int(np.argmax(scores))

    fig, ax = plt.subplots()
    ax.plot(spans, scores, "o-")
    ax.plot(spans[i_best], scores[i_best], "r*", markersize=14,
            label=f"best: b = {spans[i_best]:.2f} m, score = {scores[i_best]:.2f}")
    ax.set_xlabel("Wing span b [m]")
    ax.set_ylabel("Score [-]")
    ax.set_title("Score vs. wing span")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    plt.show()


def main():
    spans, scores = wingspan_analysis(verbose=True)
    plot_scores(spans, scores)


if __name__ == "__main__":
    main()
