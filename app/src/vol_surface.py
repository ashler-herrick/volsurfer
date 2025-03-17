import imageio
from typing import List, cast
from io import BytesIO

import numpy as np
from numpy.typing import ArrayLike
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class VolSurface:
    """
    A volatility surface that adjusts the ATM volatility with a linear skew
    and quadratic kurtosis term. The parameters vary with expiry.

    Parameters:
      atm_strike: The ATM strike price.
      dtes:       Array-like dtes (in years) for which parameters are provided.
      atm_vols:   Array-like ATM volatilities corresponding to each expiry.
      skews:      Array-like skew values corresponding to each expiry.
      kurtosis:   Array-like kurtosis values corresponding to each expiry.
    """

    def __init__(
        self,
        atm_strike: float,
        dtes: ArrayLike,
        atm_vols: ArrayLike,
        skews: ArrayLike,
        kurtosis: ArrayLike,
    ):
        self.atm_strike = atm_strike
        self.dtes = np.array(dtes)
        self.atm_vols = np.array(atm_vols)
        self.skews = np.array(skews)
        self.kurtosis = np.array(kurtosis)

    def vol(self, strike: float, dte: float) -> float:
        """
        Calculate the adjusted volatility for a given strike and expiry (dte).
        The parameters are interpolated based on the provided expiry values.
        """
        # Interpolate the parameter values at the given dte
        atm_vol = np.interp(dte, self.dtes, self.atm_vols)
        skew = np.interp(dte, self.dtes, self.skews)
        kurt = np.interp(dte, self.dtes, self.kurtosis)

        m = strike / self.atm_strike
        return atm_vol + (m - 1) * skew + (m - 1) ** 2 * kurt

    def plot_surface(self):
        """
        Plot the volatility surface in 3D over a range of strikes and expiries.

        strike_range: Array of strikes (e.g., np.linspace(80, 120, 40)).
        dte_range:    Array of expiries (in years, e.g., np.linspace(0.01, 0.5, 40)).
        """
        dte_range = np.linspace(np.min(self.dtes), np.max(self.dtes), 40)
        strike_range = np.linspace(
            int(self.atm_strike - 0.5 * self.atm_strike),
            int(self.atm_strike + 0.5 * self.atm_strike),
            40,
        )
        # Create a meshgrid for strikes and expiries
        X, Y = np.meshgrid(strike_range, dte_range)
        Z = np.empty_like(X)

        # Calculate vol at each grid point using the interpolated parameters
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                Z[i, j] = self.vol(X[i, j], Y[i, j])

        fig = plt.figure(figsize=(8, 6), dpi=128)
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))
        surf = ax.plot_surface(X, Y, Z, cmap="viridis", edgecolor="gray", alpha=0.6)
        ax.set_xlabel("Strike")
        ax.set_ylabel("DTE")
        ax.set_zlabel("Implied Volatility")
        ax.set_title("Volatility Surface")

        ax.set_zlim(bottom=0, top=np.max(Z) + 0.5)
        ax.view_init(elev=30, azim=-45)

        fig.colorbar(surf, shrink=0.5, aspect=5)
        return fig

    def evolve(
        self,
        timesteps: int,
        new_atm_vols: ArrayLike,
        new_skews: ArrayLike,
        new_kurtosis: ArrayLike,
    ):
        """
        Evolve the volatility surface parameters from current values to new values
        over a given number of timesteps.

        Parameters:
        timesteps:    The number of intermediate steps.
        new_atm_vols: New ATM volatility values (array-like, same length as self.dtes).
        new_skews:    New skew values (array-like).
        new_kurtosis: New kurtosis values (array-like).

        Yields:
        A new VolSurface instance for each timestep.
        """
        new_atm_vols = np.array(new_atm_vols)
        new_skews = np.array(new_skews)
        new_kurtosis = np.array(new_kurtosis)

        # Loop over timesteps and linearly interpolate the parameters.
        for step in range(timesteps):
            factor = step / (timesteps - 1) if timesteps > 1 else 1.0
            inter_atm_vols = (1 - factor) * self.atm_vols + factor * new_atm_vols
            inter_skews = (1 - factor) * self.skews + factor * new_skews
            inter_kurtosis = (1 - factor) * self.kurtosis + factor * new_kurtosis

            yield VolSurface(
                self.atm_strike, self.dtes, inter_atm_vols, inter_skews, inter_kurtosis
            )


def create_vol_surface_evolution_video(
    vol_surface: VolSurface, timesteps: int, new_atm_vols, new_skews, new_kurtosis
) -> List:
    """
    Evolve the vol_surface, generate a 3D plot for each step, and combine them into an MP4 video.
    Returns the video as bytes.
    """
    frames = []

    for evolved_surface in vol_surface.evolve(
        timesteps, new_atm_vols, new_skews, new_kurtosis
    ):
        # Create the figure (ensure your plot_surface returns a Figure)
        fig = evolved_surface.plot_surface()

        # Save figure to an in-memory buffer
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=128)
        buf.seek(0)
        plt.close(fig)

        # Read buffer into an image array (for imageio)
        frame = imageio.v2.imread(buf)
        # Convert RGBA to RGB if necessary
        if frame.shape[-1] == 4:
            frame = frame[..., :3]
        frames.append(frame)
    if len(frames) < 2:
        raise ValueError(
            "Error generated vol surface frames. Less than 2 frames found."
        )

    return frames
