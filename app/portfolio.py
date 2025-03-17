from typing import List, Tuple

from src.vol_surface import VolSurface, create_vol_surface_evolution_video
from src.contracts import Option, Stock
from src.portfolio import Portfolio


def build_portfolio(underlying_price: float, portfolio_options: List[dict]):
    """
    Create Stock, Options, and a Portfolio object from the session-state dictionaries.
    """
    underlying = Stock(pos=0, price=underlying_price)
    options_list = []
    for item in portfolio_options:
        opt = Option(
            flag=item["flag"],
            strike=item["strike"],
            dte=item["dte_days"],
            pos=item["pos"],
            underlying=underlying,
        )
        options_list.append(opt)
    return Portfolio(options=options_list, stock=underlying)


def calc_s_range(underlying_price: float) -> Tuple[float, float]:
    return (underlying_price * 0.8, underlying_price * 1.2)


def plot_value_evolution(
    portfolio: Portfolio,
    vol_surface: VolSurface,
    new_atm_vols,
    new_skews,
    new_kurtosis,
    elapsed_time,
    timesteps,
    S_range,
):
    """Calls the portfolio's 3D value evolution plot and returns the figure."""
    fig = portfolio.plot_value_evolution_3d(
        vol_surface,
        new_atm_vols,
        new_skews,
        new_kurtosis,
        elapsed_time,
        timesteps,
        S_range,
    )
    return fig


def plot_all_greeks(
    portfolio: Portfolio,
    vol_surface: VolSurface,
    new_atm_vols,
    new_skews,
    new_kurtosis,
    elapsed_time,
    timesteps,
    S_range,
):
    """Plot 3D evolution of delta, gamma, theta, vega, one after another."""
    figs = {}
    for greek_name in ["delta", "gamma", "theta", "vega"]:
        figs[greek_name] = portfolio.plot_greek_evolution_3d(
            vol_surface,
            new_atm_vols,
            new_skews,
            new_kurtosis,
            elapsed_time,
            timesteps,
            S_range,
            greek_name,
        )
    return figs
