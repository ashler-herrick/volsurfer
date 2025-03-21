import itertools
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

from src.vol_surface import VolSurface


class Chain:
    """
    Represents an option chain, containing both call and put options
    across different strikes and days to expiration (DTE).

    This class constructs a dataframe containing option pricing data,
    implied volatility (IV), and Greeks based on a given volatility surface.
    """

    def __init__(
        self,
        dtes: ArrayLike,
        vol_surface: VolSurface,
        underlying_price: float,
        s_range: ArrayLike,
        strike_width: int = 5,
        r: float = 0.01,
    ):
        """
        Initializes the option chain with a range of strikes and expiration dates.

        Args:
            dtes (ArrayLike): A list or array of days to expiration (DTE) for the options.
            vol_surface (VolSurface): The volatility surface used to compute IVs.
            underlying_price (float): The current price of the underlying asset.
            s_range (ArrayLike): A range of underlying asset prices to determine strike prices.
            strike_width (int, optional): The interval between consecutive strikes. Defaults to 5.
            r (float, optional): The risk-free interest rate. Defaults to 0.01 (1%).

        Attributes:
            _df (pd.DataFrame): DataFrame containing option data, including prices and Greeks.
        """
        self.vol_surface = vol_surface
        strikes = np.arange(
            round(np.min(s_range) / strike_width) * strike_width,
            round(np.max(s_range) / strike_width) * strike_width,
            strike_width,
        )
        cross = list(itertools.product(dtes, strikes, ["c", "p"]))  # type: ignore
        self._df = pd.DataFrame(cross, columns=["DTE", "Strike", "flag"])
        self._df["underlying"] = underlying_price
        self._df["t"] = self._df["DTE"] / 365  # Time to expiration in years
        self._df["IV"] = self._df.apply(
            lambda row: vol_surface.vol(row["Strike"], row["DTE"]), axis=1
        )
        self._df["r"] = r
        self._df["Type"] = self._df["flag"].map({"c": "Call", "p": "Put"})

        # Compute option prices using the Black-Scholes model
        self._df["Price"] = self._df.apply(
            lambda row: black_scholes(
                flag=row["flag"],
                S=row["underlying"],
                K=row["Strike"],
                t=row["t"],
                r=row["r"],
                sigma=row["IV"],
            ),
            axis=1,
        )

        # Compute Greeks
        self._df["Delta"] = self._df.apply(
            lambda row: delta(
                flag=row["flag"],
                S=row["underlying"],
                K=row["Strike"],
                t=row["t"],
                r=row["r"],
                sigma=row["IV"],
            ),
            axis=1,
        )
        self._df["Gamma"] = self._df.apply(
            lambda row: gamma(
                flag=row["flag"],
                S=row["underlying"],
                K=row["Strike"],
                t=row["t"],
                r=row["r"],
                sigma=row["IV"],
            ),
            axis=1,
        )
        self._df["Theta"] = self._df.apply(
            lambda row: theta(  # type: ignore
                flag=row["flag"],
                S=row["underlying"],
                K=row["Strike"],
                t=row["t"],
                r=row["r"],
                sigma=row["IV"],
            ),
            axis=1,
        )
        self._df["Vega"] = self._df.apply(
            lambda row: vega(
                flag=row["flag"],
                S=row["underlying"],
                K=row["Strike"],
                t=row["t"],
                r=row["r"],
                sigma=row["IV"],
            ),
            axis=1,
        )

    @property
    def df(self) -> pd.DataFrame:
        """
        Retrieves the formatted option chain dataframe.

        Returns:
            pd.DataFrame: A DataFrame containing the following columns:
                - "Type" (str): "Call" or "Put".
                - "Strike" (float): The option's strike price.
                - "Price" (float): The Black-Scholes calculated option price.
                - "IV" (float): Implied volatility of the option.
                - "Delta" (float): Option delta (sensitivity to underlying price changes).
                - "Gamma" (float): Option gamma (rate of change of delta).
                - "Theta" (float): Option theta (time decay).
                - "Vega" (float): Option vega (sensitivity to volatility changes).
                - "DTE" (int): Days to expiration.
        """
        return self._df[
            ["Type", "Strike", "Price", "IV", "Delta", "Gamma", "Theta", "Vega", "DTE"]
        ]
