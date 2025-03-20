import itertools

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

from src.vol_surface import VolSurface


class Chain:
    def __init__(
        self,
        dtes: ArrayLike,
        vol_surface: VolSurface,
        underlying_price: float,
        s_range: ArrayLike,
        strike_width: int = 5,
        r: float = 0.01,
    ):
        self.vol_surface = vol_surface
        strikes = np.arange(
            round(np.min(s_range) / strike_width) * strike_width,
            round(np.max(s_range) / strike_width) * strike_width,
            strike_width,
        )
        cross = list(itertools.product(dtes, strikes, ["c", "p"]))  # type: ignore
        self._df = pd.DataFrame(cross, columns=["DTE", "Strike", "flag"])
        self._df["underlying"] = underlying_price
        self._df["t"] = self._df["DTE"] / 365
        self._df["IV"] = self._df.apply(
            lambda row: vol_surface.vol(row["Strike"], row["DTE"]), axis=1
        )
        self._df["r"] = r
        self._df["Type"] = self._df["flag"].map({"c": "Call", "p": "Put"})
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
            lambda row: theta(              # type: ignore
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
        return self._df[
            ["Type", "Strike", "Price", "IV", "Delta", "Gamma", "Theta", "Vega", "DTE"]
        ]
