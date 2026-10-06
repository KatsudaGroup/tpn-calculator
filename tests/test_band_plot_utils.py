import pytest

from band_plot_utils import calc_normalized_signal


@pytest.mark.parametrize(
    "signal_raw_value, expected",
    [
        pytest.param(-10, 255, id="negative-clipped-to-zero"),
        pytest.param(0, 255, id="zero-is-white"),
        pytest.param(50, 127, id="midpoint-truncated-to-integer"),
        pytest.param(100, 0, id="upper-bound-is-black"),
        pytest.param(150, 0, id="above-upper-bound-clipped"),
    ],
)
def test_eq1_maps_clipped_signal_to_8bit_grayscale(signal_raw_value, expected):
    """Eq. 1 clips to [0, I_max], inverts, and truncates to an integer."""
    result = calc_normalized_signal(signal_raw_value, signal_upper_bound=100)

    assert result == expected
    assert isinstance(result, int)
