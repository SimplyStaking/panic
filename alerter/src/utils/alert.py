def floaty(value: str) -> float:
    if value is None or value == "None":
        return 0
    else:
        return float(value)
