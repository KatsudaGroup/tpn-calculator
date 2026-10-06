import pandas as pd
import pytest

from utilfuncs import calc_signal_sum, calc_signal_sum_positive_region


@pytest.mark.parametrize(
    "mw_min, mw_max, expected",
    [
        pytest.param(20, 40, {"A": 9, "B": 18}, id="both-boundaries-included"),
        pytest.param(None, None, {"A": 209, "B": 418}, id="no-range"),
        pytest.param(20, None, {"A": 109, "B": 218}, id="lower-bound-only"),
        pytest.param(None, 40, {"A": 109, "B": 218}, id="upper-bound-only"),
        pytest.param(30, 30, {"A": 3, "B": 6}, id="equal-boundaries"),
        pytest.param(60, 70, {"A": 0, "B": 0}, id="no-points-in-range"),
    ],
)
def test_eq2_sums_signals_within_inclusive_mw_range(mw_min, mw_max, expected):
    """Eq. 2 sums detection points in the MW range, excluding the MW column."""
    # Unsorted MW values ensure filtering does not depend on row order.
    data = pd.DataFrame(
        {"kDa": [50, 20, 40, 10, 30], "A": [100, 1, 5, 100, 3],
         "B": [200, 2, 10, 200, 6]}
    )

    result = calc_signal_sum(
        data, signal_range_min=mw_min, signal_range_max=mw_max
    )

    assert result == expected


def test_positive_region_filters_range_then_stops_before_first_negative():
    """The optional stopping mode sums from high to low MW per series."""
    data = pd.DataFrame(
        {
            "kDa": [30, 50, 20, 40, 10],
            "A": [-1, -100, 7, 5, 100],
            "B": [3, -100, 1, 5, 100],
            "C": [3, -100, 1, -1, 100],
        }
    )

    result = calc_signal_sum_positive_region(
        data, signal_range_min=20, signal_range_max=40
    )

    # A stops at 30 kDa; B has no negative in range; C stops immediately.
    # Negative values at 50 kDa are outside the range and must not stop summation.
    assert result == {"A": 5, "B": 9, "C": 0}
