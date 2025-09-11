def print_agg(title: str, agg: dict) -> None:
    """Print a human-readable aggregation summary.

    Expected input:
      agg = {
        "model_name": {"calls": int, "tokens": float, "pc_calls": float, "pc_tokens": float},
        ...
      }

    The function prints the title, each model line sorted by tokens (desc) and a TOTAL line.
    When agg is empty it prints a "(no data)" marker.
    """

    print(title)

    if not agg:
        print("(no data)")
        return

    # Sort models by tokens descending (fallback to 0.0)
    items = sorted(
        agg.items(), key=lambda kv: float(kv[1].get("tokens", 0.0)), reverse=True
    )

    total_calls = 0
    total_tokens = 0.0

    for name, data in items:
        calls = int(data.get("calls", 0))
        tokens = float(data.get("tokens", 0.0))
        pc_calls = data.get("pc_calls")
        pc_tokens = data.get("pc_tokens")

        total_calls += calls
        total_tokens += tokens

        parts = [f"{name}"]
        parts.append(f"calls={calls}")
        parts.append(f"tokens={tokens:.1f}")
        if pc_calls is not None:
            parts.append(f"pc_calls={pc_calls}")
        if pc_tokens is not None:
            parts.append(f"pc_tokens={pc_tokens}")

        print(" ".join(parts))

    # Print totals
    print(f"TOTAL calls={total_calls} tokens={total_tokens:.1f}")
