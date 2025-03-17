from typing import List, cast
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from src.vol_surface import VolSurface
from src.contracts import Option, Stock


class Portfolio:
    def __init__(self, options: List[Option], stock: Stock):
        self.options = options
        self.stock = stock
        self.value = 0

    def portfolio_greeks(self, vol_surface: VolSurface) -> dict:
        """
        Aggregate the Greeks of all options in the portfolio.
        """
        greeks_total = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}
        for option in self.options:
            g = option.greeks(vol_surface)
            for key in greeks_total:
                greeks_total[key] += option.pos * g[key]
        return greeks_total

    def portfolio_value(self, vol_surface: VolSurface) -> float:
        """
        Sum the prices of all options in the portfolio.
        """
        return sum([opt.price(vol_surface) for opt in self.options])

    def plot_greeks(self, vol_surface: VolSurface, S_range: np.ndarray):
        """
        Plot the portfolio Greeks (delta, gamma, theta, vega) as the underlying price varies.
        """
        delta_vals, gamma_vals, theta_vals, vega_vals = [], [], [], []
        original_price = self.stock.price
        for S in S_range:
            self.stock.price = S
            g = self.portfolio_greeks(vol_surface)
            delta_vals.append(g["delta"])
            gamma_vals.append(g["gamma"])
            theta_vals.append(g["theta"])
            vega_vals.append(g["vega"])
        # Reset underlying price
        self.stock.price = original_price

        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        axs[0, 0].plot(S_range, delta_vals, marker="o")
        axs[0, 0].set_title("Portfolio Delta")
        axs[0, 0].grid(True)

        axs[0, 1].plot(S_range, gamma_vals, marker="o", color="tab:orange")
        axs[0, 1].set_title("Portfolio Gamma")
        axs[0, 1].grid(True)

        axs[1, 0].plot(S_range, theta_vals, marker="o", color="tab:green")
        axs[1, 0].set_title("Portfolio Theta")
        axs[1, 0].grid(True)

        axs[1, 1].plot(S_range, vega_vals, marker="o", color="tab:red")
        axs[1, 1].set_title("Portfolio Vega")
        axs[1, 1].grid(True)

        for ax in axs.flat:
            ax.set(xlabel="Underlying Price", ylabel="Greek Value")
        plt.tight_layout()
        plt.show()

    def evolve_portfolio(
        self,
        vol_surface: VolSurface,
        new_atm_vols: List[float],
        new_skews: List[float],
        new_kurtosis: List[float],
        elapsed_time: float,
        timesteps: int,
    ):
        """
        Yield a new Portfolio at each time step, along with the evolved vol surface.

        Parameters:
        vol_surface:   The current volatility surface.
        new_atm_vols:  New ATM vol array to evolve to.
        new_skews:     New skew array to evolve to.
        new_kurtosis:  New kurtosis array to evolve to.
        elapsed_time:  Total time (in days) to simulate.
        timesteps:     Number of discrete steps.

        Yields:
        (new_portfolio, evolved_surface) at each time step.
        """
        dt = elapsed_time / timesteps
        # Keep a copy of original DTE for each option
        original_dtes = [opt.dte for opt in self.options]

        # Evolve the vol surface to get an iterator of intermediate surfaces
        evolved_surfaces = list(
            vol_surface.evolve(timesteps, new_atm_vols, new_skews, new_kurtosis)
        )

        # For each step, build a new Portfolio
        for step, surface in enumerate(evolved_surfaces):
            # Create new option objects with updated DTE
            new_options = []
            for i, opt in enumerate(self.options):
                # Decrement DTE by dt * (step+1) so that each iteration is cumulative
                new_dte = max(original_dtes[i] - dt * (step + 1), 0)

                # Create a new Option object (assumes your Option constructor takes days)
                updated_opt = Option(
                    flag=opt.flag,
                    strike=opt.strike,
                    dte=new_dte,  # updated DTE in days
                    pos=opt.pos,
                    underlying=opt.underlying,
                )
                new_options.append(updated_opt)

            # Create a new Portfolio with these updated options
            new_portfolio = Portfolio(options=new_options, stock=self.stock)

            # Yield the new portfolio and the corresponding evolved surface
            yield new_portfolio, surface

    def plot_value_evolution_3d(
        self,
        vol_surface: VolSurface,
        new_atm_vols: List[float],
        new_skews: List[float],
        new_kurtosis: List[float],
        elapsed_time: float,
        timesteps: int,
        S_range: np.ndarray,
    ):
        # Create a matrix to store portfolio values:
        evolution_matrix = np.zeros((len(S_range), timesteps))
        original_price = self.stock.price

        for i, S in enumerate(S_range):
            self.stock.price = S
            values = []
            # Use the generator version of evolve_portfolio which yields a new portfolio and evolved vol surface at each step.
            for new_port, new_vol in self.evolve_portfolio(
                vol_surface,
                new_atm_vols,
                new_skews,
                new_kurtosis,
                elapsed_time,
                timesteps,
            ):
                values.append(new_port.portfolio_value(new_vol))
            evolution_matrix[i, :] = values

        self.stock.price = original_price  # Reset underlying price

        time_axis = np.linspace(0, elapsed_time, timesteps)
        # Create meshgrid with X as underlying price and Y as time (days)
        S_mesh, T = np.meshgrid(S_range, time_axis)
        evolution_matrix_T = evolution_matrix.T  # Transpose to match meshgrid dimensions

        fig = plt.figure(figsize=(8, 6), dpi=128)
        # Create a 3D subplot using the recommended API:
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))
        surf = ax.plot_surface(
            S_mesh, T, evolution_matrix_T, cmap="viridis", edgecolor="none", alpha=0.8
        )
        ax.set_xlabel("Underlying Price")
        ax.set_ylabel("Time (days)")
        ax.set_zlabel("Portfolio Value")
        ax.view_init(elev=30, azim=-45)
        ax.set_title("3D Evolution of Portfolio Value")
        fig.colorbar(surf, shrink=0.5, aspect=5)
        return fig

    def plot_greek_evolution_3d(
        self,
        vol_surface: VolSurface,
        new_atm_vols: List[float],
        new_skews: List[float],
        new_kurtosis: List[float],
        elapsed_time: float,
        timesteps: int,
        S_range: np.ndarray,
        greek: str,
    ):
        """
        Plot a 3D surface showing the evolution of a specified greek over time
        for a range of underlying prices.

        X-axis: Underlying Price, Y-axis: Time (days), Z-axis: Greek Value.
        """
        # Create a matrix to store greek values:
        # Rows: each underlying price; Columns: each time step.
        evolution_matrix = np.zeros((len(S_range), timesteps))
        original_price = self.stock.price

        for i, S in enumerate(S_range):
            self.stock.price = S
            greek_values = []
            # Use the generator version of evolve_portfolio which yields a new portfolio and evolved vol surface at each step.
            for new_port, new_vol in self.evolve_portfolio(
                vol_surface,
                new_atm_vols,
                new_skews,
                new_kurtosis,
                elapsed_time,
                timesteps,
            ):
                g = new_port.portfolio_greeks(new_vol)
                greek_values.append(g[greek])
            evolution_matrix[i, :] = greek_values

        self.stock.price = original_price  # Reset underlying price

        time_axis = np.linspace(0, elapsed_time, timesteps)
        # Create meshgrid with X as underlying price and Y as time (days)
        S_mesh, T = np.meshgrid(S_range, time_axis)
        evolution_matrix_T = (
            evolution_matrix.T
        )  # Transpose to match meshgrid dimensions

        fig = plt.figure(figsize=(8, 6), dpi=128)
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))
        surf = ax.plot_surface(
            S_mesh, T, evolution_matrix_T, cmap="viridis", edgecolor="none", alpha=0.8
        )
        ax.set_xlabel("Underlying Price")
        ax.set_ylabel("Time (days)")
        ax.set_zlabel(f"{greek.capitalize()}")
        ax.set_title(f"3D Evolution of Portfolio {greek.capitalize()}")
        ax.view_init(elev=30, azim=-45)

        fig.colorbar(surf, shrink=0.5, aspect=5)
        return fig
