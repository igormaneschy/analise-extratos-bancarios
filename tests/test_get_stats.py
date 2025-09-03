"""
Unit tests for get_stats.print_agg
"""
from get_stats import print_agg


def test_print_agg_empty(capsys):
    title = "Empty Test"
    agg = {}
    print_agg(title, agg)
    captured = capsys.readouterr()
    assert title in captured.out
    assert "(no data)" in captured.out


def test_print_agg_non_empty(capsys):
    title = "Non Empty Test"
    # Two models with different tokens to assert sorting and totals
    agg = {
        "model_a": {"calls": 2, "tokens": 100.0, "pc_calls": 40.0, "pc_tokens": 33.3},
        "model_b": {"calls": 1, "tokens": 200.0, "pc_calls": 20.0, "pc_tokens": 66.7},
    }

    print_agg(title, agg)
    captured = capsys.readouterr()
    out = captured.out

    # Title present
    assert title in out
    # model_b has more tokens so should appear before model_a
    idx_b = out.find("model_b")
    idx_a = out.find("model_a")
    assert idx_b != -1 and idx_a != -1 and idx_b < idx_a

    # Check formatted numbers and TOTAL line
    assert "calls=3" in out or "TOTAL calls=3" in out
    assert "tokens=300.0" in out or "TOTAL calls=3" in out
