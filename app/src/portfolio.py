from typing import List, cast
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from src.vol_surface import VolSurface
from src.contracts import Option, Stock


class Portfolio:
    """
    Represents a portfolio containing financial options and an underlying stock.

    This class provides methods to compute portfolio-level Greeks, evaluate the portfolio value,
    and visualize the impact of volatility and time evolution on portfolio performance.
    """

    def __init__(self, options: List[Option], stock: Stock):
        """
        Initializes the portfolio with a list of options and a stock.

        Args:
            options (List[Option]): A list of option contracts in the portfolio.
            stock (Stock): The underlying stock associated with the portfolio.
        """
        self.options = options
        self.stock = stock
        self.value = 0

    def portfolio_greeks(self, vol_surface: VolSurface) -> dict:
        """
        Computes the aggregated Greeks for the entire portfolio.

        Args:
            vol_surface (VolSurface): The volatility surface used to calculate the Greeks.

        Returns:
            dict: A dictionary containing the aggregated Greeks for the portfolio:
                - "delta" (float): Sensitivity to the underlying asset price.
                - "gamma" (float): Rate of change of delta.
                - "theta" (float): Time decay of option value.
                - "vega" (float): Sensitivity to volatility changes.
        """
        greeks_total = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}
        for option in self.options:
            g = option.greeks(vol_surface)
            for key in greeks_total:
                greeks_total[key] += option.pos * g[key]
        return greeks_total

    def portfolio_value(self, vol_surface: VolSurface) -> float:
        """
        Calculates the total value of the portfolio based on current option prices.

        Args:
            vol_surface (VolSurface): The volatility surface used for pricing options.

        Returns:
            float: The total portfolio value.
        """
        return sum(opt.price(vol_surface) for opt in self.options)

    def plot_greeks(self, vol_surface: VolSurface, s_range: np.ndarray):
        """
        Plots the portfolio Greeks (delta, gamma, theta, vega) as the underlying price varies.

        Args:
            vol_surface (VolSurface): The volatility surface used for pricing.
            s_range (np.ndarray): A range of underlying asset prices to evaluate the Greeks.

        Returns:
            None
        """
        delta_vals, gamma_vals, theta_vals, vega_vals = [], [], [], []
        original_price = self.stock.price

        for S in s_range:
            self.stock.price = S
            g = self.portfolio_greeks(vol_surface)
            delta_vals.append(g["delta"])
            gamma_vals.append(g["gamma"])
            theta_vals.append(g["theta"])
            vega_vals.append(g["vega"])

        self.stock.price = original_price  # Reset stock price

        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        axs[0, 0].plot(s_range, delta_vals, marker="o")
        axs[0, 0].set_title("Portfolio Delta")
        axs[0, 0].grid(True)

        axs[0, 1].plot(s_range, gamma_vals, marker="o", color="tab:orange")
        axs[0, 1].set_title("Portfolio Gamma")
        axs[0, 1].grid(True)

        axs[1, 0].plot(s_range, theta_vals, marker="o", color="tab:green")
        axs[1, 0].set_title("Portfolio Theta")
        axs[1, 0].grid(True)

        axs[1, 1].plot(s_range, vega_vals, marker="o", color="tab:red")
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
        Evolves the portfolio over time by adjusting option parameters and volatility.

        Args:
            vol_surface (VolSurface): The initial volatility surface.
            new_atm_vols (List[float]): New ATM volatility values over time.
            new_skews (List[float]): New skew values over time.
            new_kurtosis (List[float]): New kurtosis values over time.
            elapsed_time (float): Total time (in days) to simulate.
            timesteps (int): Number of discrete time steps.

        Yields:
            Tuple[Portfolio, VolSurface]: A tuple containing the updated portfolio and
            the evolved volatility surface at each time step.
        """
        dt = elapsed_time / timesteps
        original_dtes = [opt.dte for opt in self.options]
        evolved_surfaces = list(
            vol_surface.evolve(timesteps, new_atm_vols, new_skews, new_kurtosis)
        )

        for step, surface in enumerate(evolved_surfaces):
            new_options = []
            for i, opt in enumerate(self.options):
                new_dte = max(original_dtes[i] - dt * (step + 1), 0)
                updated_opt = Option(
                    flag=opt.flag,
                    strike=opt.strike,
                    dte=new_dte,
                    pos=opt.pos,
                    underlying=opt.underlying,
                )
                new_options.append(updated_opt)

            new_portfolio = Portfolio(options=new_options, stock=self.stock)
            yield new_portfolio, surface

    def plot_pnl_evolution_3d(
        self,
        vol_surface: VolSurface,
        new_atm_vols: List[float],
        new_skews: List[float],
        new_kurtosis: List[float],
        elapsed_time: float,
        timesteps: int,
        s_range: np.ndarray,
    ):
        """
        Plots a 3D surface of portfolio PnL evolution over time and varying underlying prices.

        Args:
            vol_surface (VolSurface): The initial volatility surface.
            new_atm_vols (List[float]): New ATM volatility values over time.
            new_skews (List[float]): New skew values over time.
            new_kurtosis (List[float]): New kurtosis values over time.
            elapsed_time (float): Total time (in days) to simulate.
            timesteps (int): Number of discrete time steps.
            s_range (np.ndarray): A range of underlying prices.

        Returns:
            matplotlib.figure.Figure: A 3D plot of portfolio PnL evolution.
        """
        pnl_matrix = np.zeros((len(s_range), timesteps))
        original_price = self.stock.price
        init_value = self.portfolio_value(vol_surface)

        for i, S in enumerate(s_range):
            self.stock.price = S
            pnl_values = []
            for new_port, new_vol in self.evolve_portfolio(
                vol_surface,
                new_atm_vols,
                new_skews,
                new_kurtosis,
                elapsed_time,
                timesteps,
            ):
                pnl_values.append(new_port.portfolio_value(new_vol) - init_value)

            pnl_matrix[i, :] = pnl_values

        self.stock.price = original_price  # Reset stock price

        time_axis = np.linspace(0, elapsed_time, timesteps)
        S_mesh, T = np.meshgrid(s_range, time_axis)
        pnl_matrix_T = pnl_matrix.T

        fig = plt.figure(figsize=(8, 6), dpi=128)
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))
        surf = ax.plot_surface(
            S_mesh, T, pnl_matrix_T, cmap="RdYlGn", edgecolor="none", alpha=0.8
        )

        ax.set_xlabel("Underlying Price")
        ax.set_ylabel("Time (days)")
        ax.set_zlabel("PnL")
        ax.set_title("3D Evolution of Portfolio PnL")
        ax.view_init(elev=30, azim=-60)
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
        s_range: np.ndarray,
        greek: str,
    ):
        """
        Plots a 3D surface showing the evolution of a specified Greek over time
        as a function of the underlying asset's price.

        Args:
            vol_surface (VolSurface): The initial volatility surface used for pricing.
            new_atm_vols (List[float]): A list of new ATM volatility values over time.
            new_skews (List[float]): A list of new skew values over time.
            new_kurtosis (List[float]): A list of new kurtosis values over time.
            elapsed_time (float): The total simulation time in days.
            timesteps (int): The number of discrete time steps in the evolution.
            s_range (np.ndarray): An array of underlying asset prices to analyze.
            greek (str): The Greek to plot, e.g., "delta", "gamma", "theta", or "vega".

        Returns:
            matplotlib.figure.Figure: A 3D plot visualizing the evolution of the specified Greek.

        Notes:
            - The X-axis represents the underlying asset price.
            - The Y-axis represents time in days.
            - The Z-axis represents the specified Greek value.
        """
        # Create a matrix to store greek values:
        # Rows: each underlying price; Columns: each time step.
        evolution_matrix = np.zeros((len(s_range), timesteps))
        original_price = self.stock.price

        for i, S in enumerate(s_range):
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
        S_mesh, T = np.meshgrid(s_range, time_axis)
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
        ax.view_init(elev=30, azim=-60)

        fig.colorbar(surf, shrink=0.5, aspect=5)
        return fig
