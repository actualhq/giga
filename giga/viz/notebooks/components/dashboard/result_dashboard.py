import ipywidgets as widgets
import plotly.graph_objects as go
from IPython.display import display, Javascript
import plotly.express as px

from giga.viz.notebooks.data_maps.result_maps import (
    make_cost_map,
    make_technology_map,
    make_technology_average_cost_barplot,
    make_technology_total_cost_barplot,
    make_fiber_distance_map_plot,
    make_cellular_distance_map_plot,
    make_cellular_coverage_map,
)
from giga.viz.notebooks.tables import create_summary_table
from giga.viz.notebooks.components.charts.overview import (
    ProjectOverview,
    project_overview_grid,
)
from giga.viz.notebooks.components.html.sections import section
from giga.viz.notebooks.components.charts.plotters import (
    technology_distribution_bar_plot,
    cumulative_fiber_distance_barplot,
    cumulative_cell_tower_distance_barplot,
    make_cost_histogram,
    make_project_cost_bar_plots,
    make_unit_cost_bar_plot,
    make_satellite_pie_breakdown,
)
from giga.viz.colors import GIGA_TECHNOLOGY_COLORS
from giga.viz.plot_configs import STATIC_MAP_MODEBAR_CONFIG


class ResultDashboard:
    """
    Generates a dashboard for the results of a project.
    Displays the following in individual tabs:
    - Project Overview
    - Maps
    - Cost
    - Technology
    """

    def __init__(self, results, height=650):
        self.results = results
        self.height = height

    def display(self):
        tabs = widgets.Tab(
            children=[
                self.infrastructure_tab(),
                self.overview_tab(),
                self.cost_tab(),
                self.unit_cost_tab(),
            ]
        )
        tabs.set_title(0, "Infrastructure Availability")
        tabs.set_title(1, "Project Overview")
        tabs.set_title(2, "Project Cost")
        tabs.set_title(3, "Unit Costs")

        style = """
            <style>
                .widget-tab > .p-TabBar .p-TabBar-tab {
                    font-family: Verdana Bold;
                    font-weight: bold;
                    font-size: 14px;
                    background-color: lightgrey;
                    border-radius: 10px 10px 0 0;
                    padding: 5px;
                }
                .jupyter-widgets.widget-tab > .p-TabBar .p-TabBar-tab {
                    flex: 0 1 auto
                }
            </style>
        """
        display(widgets.HTML(style))
        display(tabs)

    def populate_outputs(self):
        self.overview_grid = project_overview_grid(self.results.output_project_overview)
        self.fiber_infra_map = make_fiber_distance_map_plot(self.results.new_connected_schools)
        self.fiber_distance_bar = cumulative_fiber_distance_barplot(self.results.output_cost_table)
        self.cell_infra_map = make_cellular_distance_map_plot(self.results.new_connected_schools)
        self.cell_distance_bar = cumulative_cell_tower_distance_barplot(self.results.output_cost_table)
        self.cell_coverage_map = make_cellular_coverage_map(self.results.new_connected_schools)
        self.technology_map = make_technology_map(self.results.new_connected_schools)
        self.satellite_pie_breakdown = make_satellite_pie_breakdown(self.results.new_connected_schools)
        self.per_school_cost_map = make_cost_map(
            self.results.new_connected_schools,
            cost_key="total_cost",
            display_key="Per School Cost (USD)",
            title="Average Cost Per School",
        )
        self.per_student_cost_map = make_cost_map(
            self.results.new_connected_schools,
            cost_key="total_cost_per_student",
            display_key="Per Student Cost (USD)",
            title="Average Cost Per Student",
        )
        self.total_cost_map = make_cost_map(
            self.results.new_connected_schools,
            cost_key="total_cost",
            display_key="Total Cost (USD)",
            title = "Total Cost Map"
        )
        self.total_cost_histogram = make_cost_histogram(
            self.results.new_connected_schools, cost_key="total_cost"
        )
        self.cost_per_student_map = make_cost_map(
            self.results.new_connected_schools,
            cost_key="total_cost_per_student",
            display_key="Per Student Cost (USD)",
            title="Per Student Cost"
        )
        try:
            self.cost_per_student_histogram = make_cost_histogram(
                self.results.new_connected_schools,
                cost_key="total_cost_per_student"
            )
        except:
            self.cost_per_student_histogram = None
        self.project_cost_barplot = make_project_cost_bar_plots(self.results)
        self.average_cost_barplot = make_technology_average_cost_barplot(
            self.results.new_connected_schools
        )
        self.total_cost_barplot = make_technology_total_cost_barplot(
            self.results.new_connected_schools
        )
        to_show = self.results.new_connected_schools
        self.technology_pie = px.pie(
            to_show,
            names="technology",
            color="technology",
            color_discrete_map=GIGA_TECHNOLOGY_COLORS,
        ).update_traces(
            textinfo="label+value+percent", hoverinfo="label+value+percent"
        ).update_layout(
            title={
                'text': "Number of Schools Connected by Tech Type",
                'y': 0.95,
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
        self.cost_pie = px.pie(
            to_show,
            values="total_cost",
            names="technology",
            color="technology",
            color_discrete_map=GIGA_TECHNOLOGY_COLORS,
        ).update_traces(
            textinfo="label+value+percent", hoverinfo="label+value+percent"
        ).update_layout(
            title={
                'text': "Total CapEx and OpEx by Tech Type",
                'y': 0.95,
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
        self.summary_table = create_summary_table(
            self.results.output_space, self.results.data_space
        )
        self.unit_cost_bar_plot = make_unit_cost_bar_plot(self.results)
        self.tech_pie = px.pie(to_show, names="technology").update_layout(
            title={
                'text': "Fraction of Schools Connected by Technology",
                'y': 0.95,
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
        self.tech_cost_pie = px.pie(to_show, values="total_cost", names="technology").update_layout(
            title={
                'text': "Total Cost by Technology",
                'y': 0.95,
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
        self.feasibility_pie = px.pie(self.results.output_cost_table, names="reason").update_layout(
            title={
                'text': "School Connectivity Feasibility",
                'y': 0.95,
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
        self.tech_distrib_plot = technology_distribution_bar_plot(self.results.technology_counts).update_layout(
            title={
                'text': "Technology Distribution by School",
                'y': 0.95,
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

    def get_visual_plots(self):
        # These plots will be included in downloaded reports.
        return [
            self.overview_grid,
            self.fiber_infra_map,
            self.fiber_distance_bar,
            self.cell_infra_map,
            self.cell_distance_bar,
            self.cell_coverage_map,
            self.technology_map,
            self.satellite_pie_breakdown,
            self.per_school_cost_map,
            self.per_student_cost_map,
            self.total_cost_map,
            self.total_cost_histogram,
            self.cost_per_student_map,
            self.cost_per_student_histogram,
            self.project_cost_barplot,
            self.average_cost_barplot,
            self.total_cost_barplot,
            self.technology_pie,
            self.cost_pie,
            self.summary_table,
            self.unit_cost_bar_plot,
            self.tech_pie,
            self.tech_cost_pie,
            self.feasibility_pie,
            self.tech_distrib_plot
        ]

    def _update_title_font(self, fig):
        fig.update_layout(
            title_font=dict(size=18, family="Arial", color="black")
        )

    def _figure_to_output(self, fig, layout=widgets.Layout(width="100%")):
        self._update_title_font(fig)
        output = widgets.Output(layout=layout)
        with output:
            display(fig)
        return output

    def _map_to_output(self, fig, layout=widgets.Layout(width="850px", height="650px")):
        output = widgets.Output(layout=layout)
        fig = go.FigureWidget(fig)
        fig._config = {**fig._config, **STATIC_MAP_MODEBAR_CONFIG}
        with output:
            display(fig)
        return output

    def overview_tab(self):
        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.HBox(
                    [
                        section("Project Summary", self.overview_grid, "dark"),
                        section(
                            "Schools Connected by Technology",
                            self._figure_to_output(self.tech_distrib_plot),
                            "dark",
                        ),
                    ]
                )
            )
        return tab

    def infrastructure_tab(self):
        # Fiber Infra
        fiber_plots = widgets.VBox([
            self._map_to_output(self.fiber_infra_map),
            self._figure_to_output(self.fiber_distance_bar)
        ])
        # Cell Infra
        cell_plots = widgets.VBox([
            self._map_to_output(self.cell_infra_map),
            self._figure_to_output(self.cell_distance_bar)
        ])
        # Cell Coverage
        coverage_plots = widgets.VBox([
            self._map_to_output(self.cell_coverage_map)
        ])
        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        # Technology Map
        # cost maps
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Fiber Infrastructure", fiber_plots, "dark"),
                        section("Cellular Infrastructure", cell_plots, "dark"),
                        section("Cellular Coverage", coverage_plots, "dark"),
                        section("Technology Modalities", self._map_to_output(self.technology_map), "dark"),
                        section("Satellite Only Modality", self._figure_to_output(self.satellite_pie_breakdown), "dark"),
                        section("Average Cost Per School", self._map_to_output(self.per_school_cost_map), "dark"),
                        section(
                            "Average Cost Per Student", self._map_to_output(self.per_student_cost_map), "dark"
                        ),
                    ]
                )
            )
        return tab

    def maps_tab(self):
        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.VBox(
                    [
                        section(
                            "Average Cost Per School", widgets.VBox([self.total_cost_map]), "dark"
                        ).add_class("center"),
                        section(
                            "Average Cost Per Student", widgets.VBox([self.cost_per_student_map]), "dark"
                        ).add_class("center"),
                    ]
                )
            )
        return tab

    def cost_tab(self):
        tab = widgets.Output(layout=widgets.Layout(width="100%"))
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Project Costs", self._figure_to_output(self.project_cost_barplot)),
                        section(
                            "Average per School Technology Cost", self._figure_to_output(self.average_cost_barplot)
                        ),
                        section("Total Technology Costs", self._figure_to_output(self.total_cost_barplot)),
                        section(
                            "Number of Schools Connected by Tech Type", self._figure_to_output(self.technology_pie)
                        ),
                        section("Total CapEx and OpEx by Tech Type", self._figure_to_output(self.cost_pie)),
                        section(
                            "Total Costs by CapEx, OpEx, and Electricity", self.summary_table
                        ),
                    ]
                )
            )
        return tab

    def unit_cost_tab(self):
        tab = widgets.Output()
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Unit Cost", self._figure_to_output(self.unit_cost_bar_plot)),
                    ]
                )
            )
        return tab

    def technology_tab(self):
        tab = widgets.Output()
        with tab:
            display(
                widgets.VBox(
                    [
                        section("Percent Technology", self._figure_to_output(self.tech_pie)),
                        section("Percent Cost", self._figure_to_output(self.tech_cost_pie)),
                        section("Technology Feasibility", self._figure_to_output(self.feasibility_pie)),
                    ]
                )
            )
        return tab
