class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class InvalidHourlyRateError(DomainError):
    code = "invalid_hourly_rate"


class InvalidTimerRangeError(DomainError):
    code = "invalid_timer_range"
