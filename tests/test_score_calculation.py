"""
Placeholder tests. For the moment they only show how testing works in this
project (run with `python -m pytest` from the repo root). Replace or extend
them with real checks once the team functions are implemented.
"""

import overall_inputs
from Performance import mission_sim
from Performance.score_calculation import calc_score


def test_calc_score_increases_with_mission_time():
    low = calc_score(t_mission=100.0, cost=500.0, v_stall=8.0, d_to=20.0)
    high = calc_score(t_mission=200.0, cost=500.0, v_stall=8.0, d_to=20.0)
    assert high > low


def test_calc_score_decreases_with_higher_cost():
    cheap = calc_score(t_mission=200.0, cost=400.0, v_stall=8.0, d_to=20.0)
    expensive = calc_score(t_mission=200.0, cost=800.0, v_stall=8.0, d_to=20.0)
    assert cheap > expensive


def test_mission_sim_returns_positive_takeoff_distance():
    t_mission, d_to = mission_sim.mission_sim(overall_inputs.DESIGN_VARIABLES_EXAMPLE)
    assert t_mission >= 0.0
    assert d_to > 0.0
