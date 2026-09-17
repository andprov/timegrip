def ru_plural(number: int, one: str, few: str, many: str) -> str:
    remainder = abs(number) % 100
    if 11 <= remainder <= 14:
        return many
    last_digit = remainder % 10
    if last_digit == 1:
        return one
    if 2 <= last_digit <= 4:
        return few
    return many
