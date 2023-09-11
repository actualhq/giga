import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import math

from giga.viz.colors import (
    COST_COLORS_PAIR,
    COST_COLORS_TRIPLET,
    ORDERED_CUMULATIVE_DISTANCE_COLORS,
    SATELLITE_BREAKDOWN_COLORS,
)


DEFAULT_FIBER_BINS = [0, 5_000, 10_000, 15_000, 20_000, np.inf]
DEFAULT_FIBER_NAMES = ["5km", "10km", "15km", "20km", "20km+"]

DEFAULT_CELL_BINS = [0, 1_000, 3_000, 5_000, 10_000, np.inf]
DEFAULT_CELL_NAMES = ["1km", "3km", "5km", "10km", "10km+"]


def technology_distribution_bar_plot(data):
    # data is a dictionary of technology counts
    # The data is in the form of {technology: count}
    total = sum(data.values())
    df = pd.DataFrame(list(data.items()), columns=["Technology", "Count"])
    # Calculate the percentage
    df["Percentage"] = np.round(df["Count"] / total * 100, 2)
    # Create the plot
    fig = go.Figure(
        data=[
            go.Bar(
                name="Count",
                x=df["Technology"],
                y=df["Count"],
                text=df["Count"],
                customdata=df["Percentage"],
                texttemplate="%{text}<br>%{customdata:.2f}%",
                textposition="outside",
                marker_color=["#009dff", "#59bfff", "#bfe6ff", "#e8ffff"],
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
                width=[0.4] * len(df),
            )
        ]
    )
    # Update layout
    fig.update_layout(
        title=None,
        xaxis={
            "categoryorder": "total descending",
            "tickfont": dict(size=14, color="black", family="Arial, bold"),
            "range": [-0.5, len(df)],
        },
        yaxis=dict(title="", showticklabels=False, range=[0, max(df["Count"]) * 1.25]),
        bargap=0.3,
        plot_bgcolor="rgba(255, 255, 255, 1)",
        paper_bgcolor="rgba(255, 255, 255, 1)",
        shapes=[
            dict(
                type="line",
                yref="y",
                y0=0,
                y1=0,
                xref="x",
                x0=-0.5,
                x1=len(df) - 0.5,
                line=dict(color="Black", width=2),
            )
        ],
        autosize=True,
        margin=dict(t=0, r=100, l=20, b=0),
    )
    return fig


def make_cost_histogram(results, num_bins=40, cost_key="total_cost"):
    total_cost = results[cost_key].values

    # get colors based on bins
    colorscale = px.colors.diverging.RdYlGn[::-1][2:]
    color_min, color_max = np.min(total_cost), np.max(total_cost)
    bin_colors = np.linspace(color_min, color_max, num_bins + 1)
    fig = go.FigureWidget()
    # create histogram for each bin and assign color
    for i in range(num_bins):
        mask = (total_cost >= bin_colors[i]) & (total_cost < bin_colors[i + 1])
        color_index = int(
            np.interp(bin_colors[i], (color_min, color_max), (0, len(colorscale) - 1))
        )
        bin_data = total_cost[mask]
        bin_center = (bin_colors[i] + bin_colors[i + 1]) / 2  # calculate bin center
        fig.add_trace(
            go.Histogram(
                x=bin_data,
                marker_color=colorscale[color_index],
                hoverinfo="x+y",
                nbinsx=num_bins,
                name=f"{bin_colors[i]:.2f} - {bin_colors[i+1]:.2f}",
                showlegend=False,
            )
        )
        if len(bin_data) > 0:
            fig.add_trace(
                go.Scatter(
                    x=[bin_center],
                    y=[len(bin_data)],
                    mode="text",
                    text=[str(len(bin_data))],
                    textposition="top center",
                    textfont=dict(color="white", family="Arial"),
                    showlegend=False,
                )
            )
    # customize layout
    fig.update_layout(
        title_font_color="white",
        title={
            "text": "Cost Distribution",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                family="Arial",
                size=36,
                color="white",
            ),
        },
        barmode="stack",
        plot_bgcolor="#2a2a2a",
        paper_bgcolor="#2a2a2a",
        font=dict(color="white", family="Arial"),
        autosize=True,
        width=850,
        height=600,
        xaxis_title="Total Cost (USD)",
        yaxis=dict(showgrid=False, showticklabels=False),
        xaxis=dict(color="white", title_font=dict(color="white", family="Arial")),
        showlegend=False,
    )
    return fig


def cumulative_distance_bar_plot(
    data, distance_key, distance_cutoff, bins, names, title, x_label=None, y_label=None
):
    # Use the cut function
    df = data
    df["category"] = pd.cut(df[distance_key], bins, labels=names)
    # Convert the category to a categorical datatype and sort it based on the original order
    category_counts = df["category"].value_counts().sort_index()
    cumulative_counts = category_counts.cumsum()
    cumulative_counts = cumulative_counts.reindex(names, fill_value=0)
    # Sort cumulative_counts by the names list
    cumulative_counts = cumulative_counts[names]
    percent_within = round(sum(data[distance_key] <= distance_cutoff) / len(data) * 100)
    y_labels = [label + " " for label in cumulative_counts.index[::-1]]
    # Create the plot
    fig = go.Figure(
        data=[
            go.Bar(
                name="Count",
                x=list(cumulative_counts.values[::-1]),
                y=list(y_labels),
                text=list(cumulative_counts.values[::-1]),
                orientation="h",
                textposition="outside",
                marker_color=ORDERED_CUMULATIVE_DISTANCE_COLORS,
                marker_line_color="rgb(8,48,107)",
                marker_line_width=1.5,
                opacity=0.6,
                width=[0.4] * len(cumulative_counts),
            )
        ]
    )
    # Update layout
    fig.update_layout(
        title={
            "text": f"<b>{percent_within}% of " + title + "</b>",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(
                family="Arial",
                size=18,
                color="#000000",
            ),
        },
        bargap=0.3,
        plot_bgcolor="#faf8f2",
        paper_bgcolor="#faf8f2",
        yaxis={
            "title": y_label,
            "title_font": dict(size=15, color="black", family="Arial"),
            "categoryorder": "array",
            "tickfont": dict(size=13, color="black", family="Arial"),
            "range": [-0.5, len(cumulative_counts)],
        },
        xaxis={
            "title": x_label,
            "title_font": dict(size=15, color="black", family="Arial"),
            "showticklabels": True,
            "range": [0, max(cumulative_counts.values) * 1.1],
        },
    )
    return fig


def cumulative_fiber_distance_barplot(
    data,
    distance_key="nearest_fiber",
    distance_cutoff=10_000,
    bins=DEFAULT_FIBER_BINS,
    names=DEFAULT_FIBER_NAMES,
    title="Unconnected Schools within 10km of a Fiber Node",
):
    return cumulative_distance_bar_plot(
        data, distance_key, distance_cutoff, bins, names, title,
        x_label="Number of schools within distance to a fiber node",
        y_label="Distance to node"
    )


def cumulative_cell_tower_distance_barplot(
    data,
    distance_key="nearest_cell_tower",
    distance_cutoff=3_000,
    bins=DEFAULT_CELL_BINS,
    names=DEFAULT_CELL_NAMES,
    title="Unconnected Schools within 3km of a Cell Tower",
):
    return cumulative_distance_bar_plot(
        data, distance_key, distance_cutoff, bins, names, title,
        x_label="Number of schools within distance to a cell tower",
        y_label="Distance to tower"
    )


def make_project_cost_bar_plots(stats, bar_width=0.3):
    totals_mil = stats.totals_lookup_table_mil
    averages_usd = stats.averages_lookup_table_usd
    # Create subplot figure
    fig = make_subplots(rows=1, cols=2)
    # Add first bar plot
    for i, (key, value) in enumerate(totals_mil.items()):
        fig.add_trace(
            go.Bar(
                name=key,
                x=[key],
                y=[round(value, 2)],
                marker_color=COST_COLORS_TRIPLET[i],
                text=[round(value, 2)],
                textposition="auto",
                width=[bar_width]
            ),
            row=1,
            col=1,
        )
    # Add second bar plot
    for i, (key, value) in enumerate(averages_usd.items()):
        fig.add_trace(
            go.Bar(
                name=key,
                x=[key],
                y=[round(value, 2)],
                marker_color=COST_COLORS_PAIR[i],
                text=[round(value)],
                textposition="auto",
                width=[bar_width],
            ),
            row=1,
            col=2,
        )
    # Update layout
    fig.update_layout(
        title=dict(
            text="Total Project Costs (USD Millions) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Average Total Costs (USD)",
            x=0.5, 
            font=dict(size=18, family="Arial")
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        autosize=False,
        width=1000,  # increase the figure width to provide more space between subplots
        height=500,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=20,  # increase the padding to provide more space between subplots
        ),
    )

    # Remove y-axis tick labels from first subplot
    fig.update_yaxes(showticklabels=False, row=1, col=1)
    # Remove y-axis tick labels from second subplot
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    fig.add_shape(
        dict(
            type="line",
            xref="paper",
            yref="y2",
            x0=0.55,
            y0=0,  # change here
            x1=1.0,
            y1=0,  # and here
            line=dict(
                color="Black",
                width=2,
            ),
        )
    )
    # Add horizontal line at y=0 for the second plot, slightly above y=0
    fig.add_shape(
        dict(
            type="line",
            xref="paper",
            yref="y2",
            x0=0,
            y0=0,  # change here
            x1=0.45,
            y1=0,  # and here
            line=dict(
                color="Black",
                width=2,
            ),
        )
    )
    return fig


def make_unit_cost_bar_plot(stats):
    data = stats.unit_costs
    ORDERED_COST_COLORS = ["#d8e4e8", "#AFD3E2", "#19A7CE", "#146C94"]
    TECHNOLOGY_ORDER = ["Fiber", "P2P", "LEOs", "Cellular"]

    # Creating a categorical type for ordering
    cat_type = CategoricalDtype(categories=TECHNOLOGY_ORDER, ordered=True)

    fig = make_subplots(rows=1, cols=2)

    for idx, (cost_type, costs) in enumerate(data.items()):
        df = pd.DataFrame(
            [(k, v["cost"], v["label"]) for k, v in costs.items()],
            columns=["Type", "Cost", "Label"],
        )
        df["Type"] = df["Type"].astype(cat_type)
        df = df.sort_values("Type")
        max_value = df["Cost"].max()
        for i, row in df.iterrows():
            fig.add_trace(
                go.Bar(
                    name=row["Type"],
                    x=[row["Cost"]],
                    y=[row["Label"]],
                    marker_color=ORDERED_COST_COLORS[i],
                    text=[row["Cost"]],
                    textposition="auto",
                    orientation="h",
                    width=[0.5],
                    showlegend=False,
                ),
                row=1,
                col=idx + 1,
            )
        fig.update_yaxes(
            autorange="reversed", row=1, col=idx + 1
        )  # reverse y-axis to make 'Fiber' on top
        fig.update_xaxes(range=[0, max_value * 1.25], visible=False, row=1, col=idx + 1)

    fig.update_layout(
        barmode="group",
        plot_bgcolor="white",
        yaxis=dict(automargin=True),
        yaxis2=dict(automargin=True),
        width=1000,
        height=600,
        autosize=False,
        title={
            'text': "Upfront cost by Technology (USD) &nbsp;&nbsp;&nbsp;  &nbsp;&nbsp;&nbsp; Ongoing Costs ($/Mbps a year)",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                family="Arial",
                size=18,
                color="black"
            )
        }
    )
    return fig


def make_satellite_pie_breakdown(to_show):
    # Create a new column to classify technologies as "Satellite" or "Other"
    to_show["tech_class"] = to_show["technology"].apply(
        lambda x: "Satellite" if x == "Satellite" else "Other"
    )
    # Get the count for each class
    grouped = to_show["tech_class"].value_counts().reset_index()
    grouped.columns = ["tech_class", "total"]
    # Calculate the percentage for each class
    grouped["percentage"] = (grouped["total"] / grouped["total"].sum()) * 100
    # Create a pie chart
    fig = px.pie(
        grouped,
        values="total",
        names="tech_class",
        color="tech_class",
        color_discrete_map=SATELLITE_BREAKDOWN_COLORS,
    )
    # Show the total counts and percentages on the plot
    fig.update_traces(textinfo="label+value+percent", hoverinfo="label+value+percent")
    # Add title to the plot
    fig.update_layout(
        title={
            "text": "<b>Satellite Only Viable Modality</b>",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=24, color="black", family="Arial"),
        },
        showlegend=False,
        margin=dict(t=100),
    )  # Adjust top margin to fit title)
    return fig
