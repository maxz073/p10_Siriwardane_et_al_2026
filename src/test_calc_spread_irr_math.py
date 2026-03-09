"""
Unit tests for calc_spread IRR formula: _irr_series.

Verifies numerator/denominator formula, handling of d1 <= 0 and invalid denominator.
"""

import numpy as np
import pandas as pd

from calc_spread import _irr_series


def test_irr_series_applies_formula_and_masks_invalid_rows():
    """_irr_series returns bps where denom > 0 and d1 > 0; NaN otherwise."""
    idx = pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07"])
    merged = pd.DataFrame(index=idx)

    m = pd.DataFrame(
        {
            "Ae": [1.0, 1.0, 1.0, 1.0],
            "Ic": [0.0, 0.0, 0.0, 10.0],
            "d1": [0.5, 0.0, 0.5, 0.5],  # row 2 invalid: d1 <= 0
            "d2": [0.0, 0.0, 0.0, 6.0],  # row 4 invalid: denominator <= 0
        },
        index=idx,
    )
    P = pd.Series([100.0, 100.0, 100.0, 100.0], index=idx)
    Ab = pd.Series([1.0, 1.0, 1.0, 1.0], index=idx)
    F = pd.Series([102.0, 102.0, 98.0, 102.0], index=idx)
    CF = pd.Series([1.0, 1.0, 1.0, 1.0], index=idx)

    out = _irr_series(merged=merged, m=m, P=P, Ab=Ab, F=F, CF=CF)

    expected_row_1 = ((102.0 + 1.0 - 101.0) * 10_000) / (0.5 * 101.0)
    expected_row_3 = ((98.0 + 1.0 - 101.0) * 10_000) / (0.5 * 101.0)

    assert np.isclose(out.loc[idx[0]], expected_row_1)
    assert np.isclose(out.loc[idx[2]], expected_row_3)
    assert np.isnan(out.loc[idx[1]])
    assert np.isnan(out.loc[idx[3]])
