import numpy as np
from numpy.typing import ArrayLike

from contracts import Option, Stock
from vol_surface import VolSurface


class Chain:

    def __init__(self, dtes: ArrayLike, vol_surface: VolSurface, underlying: Stock, s_range: ArrayLike, strike_width: int = 5):
        self.strikes = np.linspace(np.min(s_range), np.max(s_range), strike_width)
        self.vol_surface = vol_surface
        self.chain = {
            (dte, strike, flag) : Option(flag, strike, dte, 0, underlying)
            for dte in dtes 
            for strike in self.strikes
            for flag in ["c", "p"]
        }