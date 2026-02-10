import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def plot_simulation_progress(domain, bar_width=15):
    url = "https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/refs/heads/main/CMIP6_downscaling_plans.csv"
    url = "CMIP6_downscaling_plans.csv"
    data = pd.read_csv(url)
    if domain != 'all':
        #domain_data = data.query("domain_id == @domain and comments.str.contains('#EURbalanced')").copy()
        domain_data = data.query("domain_id == @domain").copy()
    else:
        domain_data = data.copy()
    domain_data = domain_data.query("~comments.str.contains('#ESD', na = False)").copy()
    valid_status = ['planned', 'running', 'completed']
    domain_data = domain_data.query("status in @valid_status").copy()

    domain_data['estimated_completion_date'] = pd.to_datetime(
        domain_data['estimated_completion_date'], errors='coerce'
    )

    now = pd.Timestamp.now()
    #now = pd.Timestamp('2024-01-28')
    future_completed_simulations = domain_data.query("status == 'completed' and estimated_completion_date > @now")
    if not future_completed_simulations.empty:
        print(f"Warning: {len(future_completed_simulations)} completed simulations have dates in the future:")
        print(future_completed_simulations)
    past_incomplete_simulations = domain_data.query("status != 'completed' and estimated_completion_date < @now")
    if not past_incomplete_simulations.empty:
        print(f"Warning: {len(past_incomplete_simulations)} uncomplete simulations have dates in the past:")
        print(past_incomplete_simulations)

    # Handle simulations with past estimated completion dates
    future_date = now + pd.DateOffset(months=6)
    last_date = domain_data['estimated_completion_date'].max()
    domain_data.loc[
        (domain_data['status'] == 'running') & 
        (domain_data['estimated_completion_date'] < now),
        'estimated_completion_date'
    ] = future_date

    domain_data.loc[
        (domain_data['status'] == 'planned') & 
        (domain_data['estimated_completion_date'] < now),
        'estimated_completion_date'
    ] = last_date 

    domain_data = domain_data.sort_values(by='estimated_completion_date')
    domain_data['cumulative_count'] = range(1, len(domain_data) + 1)

    # Count the simulations by status
    status_counts = domain_data['status'].value_counts()
    completed_count = status_counts.get('completed', 0)
    running_count = status_counts.get('running', 0)
    planned_count = status_counts.get('planned', 0)

    # Create the plot
    fig, ax1 = plt.subplots(figsize=(9, 4.5))

    # Step plot for cumulative simulations
    ax1.step(
        domain_data['estimated_completion_date'], 
        domain_data['cumulative_count'], 
        where='post', 
        label='Cumulative Simulations'
    )
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Cumulative Simulations')

    # Create a single stacked bar for today's counts
    heights = [completed_count, running_count, planned_count]
    colors = ['black', '#009900', '#F54d4d']
    labels = ['Completed', 'Running', 'Planned']

    # Draw the stacked bar segments
    bottom = 0
    for height, color, label in zip(heights, colors, labels):
        ax1.bar(
            x=now, 
            height=height, 
            width=bar_width, 
            bottom=bottom, 
            color=color, 
            edgecolor='none', 
            label=label
        )
        bottom += height  # Update the bottom for the next segment

    # Add a secondary y-axis that mirrors the primary y-axis
    ax2 = ax1.twinx()
    ax2.set_ylim(ax1.get_ylim())  # Mirror the limits of the primary y-axis

    ax1.legend(loc='upper left')
    plt.title(f'Cumulative number of simulations over time (CORDEX Domain: {domain})')
    plt.tight_layout()
    plt.savefig('docs/ecd_series.svg')
    # Show the plot
    #plt.show()

# Example usage:
#plot_simulation_progress(domain="MED-12", bar_width=25)
#plot_simulation_progress(domain="EUR-12", bar_width=25)
plot_simulation_progress(domain="all", bar_width=25)

