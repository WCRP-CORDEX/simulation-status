#!/usr/bin/env python3
"""Pivot SSP simulations per domain showing unique models and counts by status.

Outputs an HTML table showing per domain:
- Number of unique source_ids (RCMs)
- Number of unique driving_source_ids (GCMs)
- Number of simulations by status (for ssp experiments), color-coded
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def load_data(path: Path, collapse_resolution: bool = True) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[~df["comments"].fillna("").str.contains("#ESD", case=False)]
    ssp_sims = df[df["driving_experiment_id"].str.startswith("ssp", na=False)].copy()
    # Optionally collapse resolution (e.g., SEA-12 -> SEA)
    if collapse_resolution:
        ssp_sims["domain_id"] = ssp_sims["domain_id"].str.split('-').str[0]
    return ssp_sims

def summarize(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Group by domain and status
    grouped = (
        df.groupby(["domain_id", "status"], dropna=False)
        .agg(
            n_simulations=("domain_id", "size"),
            n_unique_rcms=("source_id", "nunique"),
            n_unique_gcms=("driving_source_id", "nunique"),
        )
        .reset_index()
    )
    
    # Pivot to have status as columns
    pivot = grouped.pivot(
        index="domain_id",
        columns="status",
        values=["n_simulations", "n_unique_rcms", "n_unique_gcms"]
    ).reset_index()
    
    # Group by domain and scenario
    scenario_grouped = (
        df.groupby(["domain_id", "driving_experiment_id"], dropna=False)
        .size()
        .reset_index(name="count")
    )
    
    # Pivot to have scenarios as columns
    scenario_pivot = scenario_grouped.pivot(
        index="domain_id",
        columns="driving_experiment_id",
        values="count"
    ).reset_index().fillna(0)
    
    # Also get overall unique counts per domain
    overall = (
        df.groupby("domain_id")
        .agg(
            total_rcms=("source_id", "nunique"),
            total_gcms=("driving_source_id", "nunique"),
            total_sims=("domain_id", "size")
        )
        .reset_index()
    )
    
    return pivot, scenario_pivot, overall


def to_html_table(pivot: pd.DataFrame, scenario_pivot: pd.DataFrame, overall: pd.DataFrame) -> str:
    # Define status order: published, completed, running, planned
    status_order = ['published', 'completed', 'running', 'planned']
    
    # Get status values from columns, ensuring all expected statuses are included
    existing_statuses = set()
    if hasattr(pivot.columns, 'levels'):
        existing_statuses = set(s for s in pivot.columns.levels[1] if s != '')
    
    # Use defined order, including statuses even if they have zero counts
    statuses = [s for s in status_order if s in existing_statuses or s == 'published']
    
    # Get scenarios from scenario_pivot columns (excluding domain_id)
    scenarios = [col for col in scenario_pivot.columns if col != 'domain_id']
    scenarios = sorted(scenarios)  # Sort alphabetically
    
    # Start HTML with CSS
    html = ['<style>']
    html.append('span.planned {color: #F54d4d; font-weight: bold}')
    html.append('span.running {color: #009900; font-weight: bold}')
    html.append('span.completed {color: #17202a; font-weight: bold}')
    html.append('span.published {color: #3399FF; font-weight: bold}')
    html.append('table {border-collapse: collapse; font-family: Arial, sans-serif; width: 100%; table-layout: fixed;}')
    html.append('th, td {border: 1px solid #ddd; padding: 8px; text-align: center; width: auto;}')
    html.append('th {background-color: #f2f2f2; font-weight: bold;}')
    html.append('th.scenario, td.scenario {background-color: #e8f4f8;}')
    html.append('</style>')
    html.append('<table>')
    
    # Build header
    html.append('<thead><tr>')
    html.append('<th>Domain</th>')
    html.append('<th>RCMs</th>')
    html.append('<th>Driving GCMs</th>')
    html.append('<th>Total Sims</th>')
    # Add scenario columns
    for scenario in scenarios:
        html.append(f'<th class="scenario">{scenario}</th>')
    # Add status columns
    for status in statuses:
        html.append(f'<th><span class="{status}">{status.capitalize()}</span></th>')
    html.append('</tr></thead>')
    
    # Build rows
    html.append('<tbody>')
    for _, domain_row in overall.iterrows():
        domain = domain_row["domain_id"]
        html.append('<tr>')
        html.append(f'<td>{domain}</td>')
        html.append(f'<td>{int(domain_row["total_rcms"])}</td>')
        html.append(f'<td>{int(domain_row["total_gcms"])}</td>')
        html.append(f'<td>{int(domain_row["total_sims"])}</td>')
        
        # Add scenario counts
        if not scenario_pivot.empty and domain in scenario_pivot["domain_id"].values:
            scenario_row = scenario_pivot[scenario_pivot["domain_id"] == domain].iloc[0]
            for scenario in scenarios:
                count = int(scenario_row[scenario]) if scenario in scenario_row else 0
                html.append(f'<td class="scenario">{count}</td>')
        else:
            for _ in scenarios:
                html.append('<td class="scenario">0</td>')
        
        # Add simulation counts by status with color coding
        for status in statuses:
            count = 0
            if not pivot.empty and domain in pivot["domain_id"].values:
                pivot_row = pivot[pivot["domain_id"] == domain].iloc[0]
                try:
                    val = pivot_row[("n_simulations", status)]
                    count = int(val) if pd.notna(val) else 0
                except (KeyError, IndexError):
                    count = 0
            
            # Always apply color span, even for zeros
            html.append(f'<td><span class="{status}">{count}</span></td>')
        
        html.append('</tr>')
    html.append('</tbody>')
    html.append('</table>')
    
    return '\n'.join(html)


def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate SSP simulation pivot table by domain"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Keep resolution in domain names"
    )
    args = parser.parse_args()
    
    csv_path = Path("CMIP6_downscaling_plans.csv")
    
    # Determine output file name based on detail level
    if args.detailed:
        output_path = Path("docs/CORDEX-CMIP6_summary_table_detailed.html")
    else:
        output_path = Path("docs/CORDEX-CMIP6_summary_table.html")
    
    # Load data with or without resolution collapse
    collapse_resolution = not args.detailed
    ssp_data = load_data(csv_path, collapse_resolution=collapse_resolution)
    pivot, scenario_pivot, overall = summarize(ssp_data)
    html = to_html_table(pivot, scenario_pivot, overall)

    # Write to file and echo to stdout for quick inspection
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"Output written to: {output_path}")
    print(html)


if __name__ == "__main__":
    main()
