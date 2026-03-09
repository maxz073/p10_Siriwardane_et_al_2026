from pathlib import Path
import sys


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from calc_spread import _parse_contract_month_yr


def test_parse_contract_month_yr_simple_cases():
    assert _parse_contract_month_yr("MAR 25") == (2025, 3)
    assert _parse_contract_month_yr('"jun 2030"') == (2030, 6)
    assert _parse_contract_month_yr("BAD 25") is None
    assert _parse_contract_month_yr(None) is None
