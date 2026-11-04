#!/usr/bin/env python3
"""Plot CORDEX-CORE progress as 3x3 GCM/RCM grids on a global map.

Usage: python scripts/global_progress_map_core.py <experiment>  (e.g. ssp370, historical)
"""
from pathlib import Path
import glob
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd


DATA_PATHS = (Path("CMIP6_downscaling_plans_merged.csv"), Path("CMIP6_downscaling_plans.csv"))

GCM_ROWS = (
    ("EC-Earth3-Veg", "EC-Earth3-Veg", "E"),
    ("MPI-ESM1-2-H", "MPI-ESM1-2-H", "M"),
    ("NorESM2-MM", "NorESM2-MM", "N"),
)
RCM_COLUMNS = (
    ("HadREM", "HadREM", "H"),
    ("RegCM", "RegCM", "R"),
    ("WRF", "WRF", "W"),
)
STATUSES = ("published", "completed", "running", "planned")
STATUS_PRIORITY = {"published": 0, "completed": 1, "running": 2, "planned": 3}
STATUS_COLORS = {
    "published": "#3399FF",
    "completed": "#000000",
    "running": "#009900",
    "planned": "#FF9999",
}
MISSING_COLOR = "#F2F2F2"
BOUNDARY_COLOR = "#6E6E6E"

DOMAIN_CENTERS = {
    "SAM": (0.35, 0.30),
    "CAM": (0.32, 0.55),
    "NAM": (0.25, 0.80),
    "EUR": (0.53, 0.83),
    "AFR": (0.52, 0.47),
    "WAS": (0.70, 0.60),
    "EAS": (0.83, 0.75),
    "SEA": (0.84, 0.52),
    "AUS": (0.90, 0.34),
}

GRID_SIZE = 0.05
CELL_GAP = 0.00
DOMAIN_LABEL_Y_OFFSET = 0.04


def load_simulations(experiment: str) -> pd.DataFrame:
    data_path = next((path for path in DATA_PATHS if path.exists()), None)
    if data_path is None:
        raise FileNotFoundError(
            "Could not find CMIP6_downscaling_plans_merged.csv or "
            "CMIP6_downscaling_plans.csv in the current directory."
        )

    simulations = pd.read_csv(data_path)
    comments = simulations["comments"].fillna("")
    mask = (
        comments.str.contains("#CORDEX-CORE", regex=False)
        & ~comments.str.contains("#ESD", regex=False)
        & simulations["driving_experiment_id"].str.lower().str.startswith(experiment.lower(), na=False)
        & simulations["domain_id"].notna()
        & simulations["driving_source_id"].notna()
        & simulations["source_id"].notna()
        & simulations["status"].isin(STATUSES)
    )
    return simulations.loc[mask].copy()


def classify_simulations(simulations: pd.DataFrame) -> dict[tuple[str, str, str], str]:
    """Map each domain/GCM/RCM category to its least-complete matching status."""
    cells: dict[tuple[str, str, str], list[str]] = {}
    for row in simulations.itertuples(index=False):
        domain = row.domain_id.split("-", maxsplit=1)[0]
        if domain not in DOMAIN_CENTERS:
            continue

        gcm = next(
            (
                gcm_key
                for gcm_key, gcm_match, _ in GCM_ROWS
                if gcm_match in row.driving_source_id
            ),
            None,
        )
        rcm = next(
            (
                rcm_key
                for rcm_key, rcm_match, _ in RCM_COLUMNS
                if rcm_match.lower() in row.source_id.lower()
            ),
            None,
        )
        if gcm is None or rcm is None:
            continue

        cells.setdefault((domain, gcm, rcm), []).append(row.status)

    return {
        key: max(statuses, key=STATUS_PRIORITY.__getitem__)
        for key, statuses in cells.items()
    }


def plot_domain_boundaries(ax) -> None:
    for border_file in glob.glob("CORDEX_domain_borders/CORDEX_*_border.dat"):
        domain = Path(border_file).name.removeprefix("CORDEX_").removesuffix("-44_border.dat")
        if domain not in DOMAIN_CENTERS:
            continue
        border = pd.read_csv(border_file, sep=r"\s+", header=None)
        ax.plot(
            *border.values.T,
            "-",
            color=BOUNDARY_COLOR,
            linewidth=1.5,
            transform=ccrs.PlateCarree(),
            zorder=1,
        )


def draw_domain_grid(
    ax,
    domain: str,
    statuses: dict[tuple[str, str, str], str],
    axes_aspect: float,
) -> None:
    center_x, center_y = DOMAIN_CENTERS[domain]
    cell_width = (GRID_SIZE - 2 * CELL_GAP) / 3
    cell_height = cell_width * axes_aspect
    cell_gap_y = CELL_GAP * axes_aspect
    grid_height = GRID_SIZE * axes_aspect
    left = center_x - GRID_SIZE / 2
    bottom = center_y - grid_height / 2

    ax.text(
        center_x,
        center_y + DOMAIN_LABEL_Y_OFFSET * axes_aspect,
        domain,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        zorder=5,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none", "pad": 0.4},
    )

    for row_index, (gcm, _, _) in enumerate(GCM_ROWS):
        for column_index, (rcm, _, _) in enumerate(RCM_COLUMNS):
            x = left + column_index * (cell_width + CELL_GAP)
            y = bottom + (2 - row_index) * (cell_height + cell_gap_y)
            status = statuses.get((domain, gcm, rcm))
            ax.add_patch(
                Rectangle(
                    (x, y),
                    cell_width,
                    cell_height,
                    transform=ax.transAxes,
                    facecolor=STATUS_COLORS.get(status, MISSING_COLOR),
                    edgecolor="white",
                    linewidth=0.6,
                    zorder=4,
                )
            )

    for column_index, (_, _, label) in enumerate(RCM_COLUMNS):
        ax.text(
            left + (column_index + 0.5) * cell_width + column_index * CELL_GAP,
            bottom + grid_height + 0.001 * axes_aspect,
            label,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=6,
            fontweight="bold",
            zorder=5,
        )

    for row_index, (_, _, label) in enumerate(GCM_ROWS):
        ax.text(
            left - 0.002,
            bottom
            + (2 - row_index + 0.5) * cell_height
            + (2 - row_index) * cell_gap_y,
            label,
            transform=ax.transAxes,
            ha="right",
            va="center",
            fontsize=6,
            fontweight="bold",
            zorder=5,
        )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    experiment = sys.argv[1]
    output_path = Path(
        f"docs/CORDEX_CMIP6_global_progress_map__{experiment}__core_3x3.svg"
    )

    simulations = load_simulations(experiment)
    cell_statuses = classify_simulations(simulations)
    if not cell_statuses:
        raise ValueError(f"No matching CORDEX-CORE {experiment} simulations were found.")

    figure = plt.figure(figsize=(16, 10))
    ax = plt.axes(projection=ccrs.Robinson())
    ax.add_feature(cfeature.LAND, facecolor="#ADF0D8")
    ax.set_global()
    plot_domain_boundaries(ax)

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=STATUS_COLORS[status], label=status.capitalize())
        for status in STATUSES
    ]
    legend_handles.append(
        Rectangle((0, 0), 1, 1, facecolor=MISSING_COLOR, edgecolor="#999999", label="Not planned")
    )
    ax.legend(
        handles=legend_handles,
        loc="lower left",
        framealpha=0.9,
        prop={"size": 9},
        title_fontsize=10,
    )

    ax.set_title(
        f"CORDEX-CORE {experiment} simulation progress by GCM (rows) and RCM (cols)",
        fontsize=14,
        fontweight="bold",
    )
    figure.tight_layout()
    figure.canvas.draw()
    axes_aspect = ax.bbox.width / ax.bbox.height
    for domain in DOMAIN_CENTERS:
        draw_domain_grid(ax, domain, cell_statuses, axes_aspect)

    for path in (output_path, output_path.with_suffix(".png")):
        figure.savefig(path, bbox_inches="tight", dpi=300)
        print(f"Map saved to {path}")


if __name__ == "__main__":
    main()
