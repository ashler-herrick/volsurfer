from py_vollib.black_scholes.greeks.numerical import delta, gamma, theta, vega
from py_vollib.black_scholes import black_scholes

# Global risk-free rate
_risk_free_rate = 0.04  # Default value (1%)


def set_risk_free_rate(r: float) -> None:
    """
    Set the global risk-free rate.
    """
    global _risk_free_rate
    _risk_free_rate = r


class Stock:
    def __init__(self, pos: int, price: float):
        self.pos = pos
        self.price = price


class Option:
    """
    A unified option class that can represent a call or a put based on the flag.

    Attributes:
      flag: 'c' for call or 'p' for put.
      strike: Option strike price.
      dte: Days to expiry.
      t: Time to expiry in years.
      pos: Position size (positive for long, negative for short).
      underlying: A Stock instance representing the underlying.
    """

    def __init__(
        self, flag: str, strike: float, dte: float, pos: int, underlying: Stock
    ):
        self.flag = flag.lower()  # "c" for call, "p" for put
        self.strike = strike
        self.dte = dte
        self.t = dte / 365.0  # Convert days to years
        self.pos = pos
        self.underlying = underlying

    def price(self, vol_surface) -> float:
        """
        Price the option using the Black-Scholes model and the given volatility surface.

        Parameters:
          vol_surface: An instance of VolSurface that provides the adjusted volatility.

        Returns:
          The option price (adjusted by position).
        """
        vol = vol_surface.vol(self.strike, self.dte)
        return self.pos * black_scholes(
            self.flag, self.underlying.price, self.strike, self.t, _risk_free_rate, vol
        )

    def greeks(self, vol_surface) -> dict:
        """
        Calculate the option Greeks using the Black-Scholes model.

        Parameters:
          vol_surface: An instance of VolSurface to get the adjusted volatility.

        Returns:
          A dictionary containing 'delta', 'gamma', 'theta', and 'vega'.
        """
        vol = vol_surface.vol(self.strike, self.dte)
        S = self.underlying.price if self.underlying else 100.0
        return {
            "delta": delta(self.flag, S, self.strike, self.t, _risk_free_rate, vol),
            "gamma": gamma(self.flag, S, self.strike, self.t, _risk_free_rate, vol),
            "theta": theta(self.flag, S, self.strike, self.t, _risk_free_rate, vol),
            "vega": vega(self.flag, S, self.strike, self.t, _risk_free_rate, vol),
        }
