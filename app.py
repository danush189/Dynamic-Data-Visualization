import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from data_service import DataService
import base64
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize data service
data_service = DataService(os.getenv("AWS_ACCESS_KEY_ID"),os.getenv("AWS_SECRET_ACCESS_KEY"))

# Default S3 bucket and prefix
BUCKET_NAME = "ieee-dataport"
DEFAULT_PREFIX = "data/1292651/EVChargeStationUseSept2018toAug2019nd.xlsx"

# Load initial dataset
data_service.load_dataset_from_s3(BUCKET_NAME, DEFAULT_PREFIX)

# Initialize Dash App with Bootstrap theme
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True
)

# Custom CSS for IEEE-like styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>IEEE Dataport Visualization Platform</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --primary-color: #0056b3;
                --secondary-color: #4a90e2;
                --light-gray: #f8f9fa;
                --dark-gray: #343a40;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
            }
            .navbar {
                background-color: var(--primary-color);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .navbar-brand {
                font-weight: bold;
                color: white !important;
            }
            .card {
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                border: none;
            }
            .card-header {
                background-color: var(--light-gray);
                border-bottom: 1px solid #eaeaea;
                font-weight: 600;
                padding: 15px 20px;
            }
            .main-content {
                padding: 30px 0;
            }
            .btn-primary {
                background-color: var(--primary-color);
                border-color: var(--primary-color);
            }
            .btn-primary:hover {
                background-color: #004494;
                border-color: #004494;
            }
            .footer {
                background-color: var(--dark-gray);
                color: white;
                padding: 20px 0;
                margin-top: 40px;
            }
            .form-control, .form-select {
                border-radius: 6px;
                border: 1px solid #ced4da;
            }
            .graph-container {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout
def serve_layout():
    # Get column classifications
    categorical_cols, numerical_cols = data_service.classify_columns()
    
    return html.Div([
        # Navigation Bar
        dbc.Navbar(
            dbc.Container([
                html.A(
                    dbc.Row([
                        dbc.Col(html.I(className="fas fa-chart-line me-2"), width="auto"),
                        dbc.Col(dbc.NavbarBrand("IEEE Dataport Visualization Platform"), width="auto")
                    ], align="center"),
                    href="#",
                    style={"textDecoration": "none"}
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink("Home", href="#")),
                        dbc.NavItem(dbc.NavLink("Documentation", href="#")),
                        dbc.NavItem(dbc.NavLink("About", href="#"))
                    ], className="ms-auto"),
                    id="navbar-collapse",
                    navbar=True
                ),
            ], fluid=True),
            color="primary",
            dark=True,
            className="mb-4"
        ),
        
        # Main Content
        dbc.Container([
            # Data Source Configuration
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-database me-2"), "Data Source"]),
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("S3 Bucket", className="fw-bold"),
                            dbc.Input(id="bucket-name", value=BUCKET_NAME, type="text"),
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Dataset Path", className="fw-bold"),
                            dbc.Input(id="data-prefix", value=DEFAULT_PREFIX, type="text"),
                        ], md=6),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([], md=9),
                        dbc.Col([
                            dbc.Button("Load Data", id="load-data-btn", color="primary", className="w-100")
                        ], md=3),
                    ]),
                    html.Div(id="load-data-output", className="mt-3")
                ])
            ], className="mb-4"),
            
            # Data Visualization Configuration
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-chart-bar me-2"), "Visualization Settings"])
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Select X-axis (Categorical/Date)", className="fw-bold"),
                            dcc.Dropdown(
                                id="x-axis",
                                options=[{"label": col, "value": col} for col in categorical_cols],
                                value=categorical_cols[0] if categorical_cols else None,
                                clearable=False,
                            ),
                        ], md=4),

                        dbc.Col([
                            dbc.Label("Select Y-axis (Numerical)", className="fw-bold"),
                            dcc.Dropdown(
                                id="y-axis",
                                options=[{"label": col, "value": col} for col in numerical_cols],
                                value=numerical_cols[0] if numerical_cols else None,
                                clearable=False,
                            ),
                        ], md=4),

                        dbc.Col([
                            dbc.Label("Select Color Key", className="fw-bold"),
                            dcc.Dropdown(
                                id="key-column",
                                options=[{"label": col, "value": col} for col in numerical_cols],
                                value=numerical_cols[1] if len(numerical_cols) > 1 else None,
                                clearable=True,
                            ),
                        ], md=4),
                    ]),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Chart Type", className="fw-bold"),
                            dbc.ButtonGroup([
                                dbc.Button(
                                    [html.I(className="fas fa-chart-scatter me-2"), "Scatter Plot"], 
                                    id="scatter-btn", 
                                    color="primary",
                                    outline=False,
                                    n_clicks=1,
                                    className="me-2"
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-chart-bar me-2"), "Bar Chart"], 
                                    id="bar-btn", 
                                    color="primary", 
                                    outline=True,
                                    n_clicks=0,
                                    className="me-2"
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-chart-line me-2"), "Line Chart"], 
                                    id="line-btn", 
                                    color="primary", 
                                    outline=True,
                                    n_clicks=0
                                ),
                            ], className="mb-3")
                        ], md=6),
                        
                        dbc.Col([
                            dbc.Label("Theme", className="fw-bold"),
                            dbc.Select(
                                id="chart-theme",
                                options=[
                                    {"label": "Default", "value": "plotly"},
                                    {"label": "Clean White", "value": "plotly_white"},
                                    {"label": "Dark", "value": "plotly_dark"},
                                ],
                                value="plotly_white",
                            )
                        ], md=6),
                    ]),
                ])
            ], className="mb-4"),
            
            # Chart Display
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-chart-pie me-2"), "Data Visualization"]),
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button(
                                html.I(className="fas fa-download"),
                                id="download-btn",
                                color="link",
                                size="sm", 
                                className="p-0 border-0",
                            ),
                            dbc.Tooltip("Download Chart", target="download-btn"),
                            dbc.Button(
                                html.I(className="fas fa-expand"),
                                id="expand-btn",
                                color="link",
                                size="sm",
                                className="p-0 border-0 ms-2",
                            ),
                            dbc.Tooltip("Expand Chart", target="expand-btn"),
                        ]),
                    ], style={"float": "right"})
                ], className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    html.Div([
                        dcc.Loading(
                            dcc.Graph(
                                id="interactive-graph",
                                config={
                                    'displayModeBar': True,
                                    'toImageButtonOptions': {
                                        'format': 'png',
                                        'filename': 'data_visualization',
                                        'height': 800,
                                        'width': 1200,
                                        'scale': 2
                                    }
                                },
                                style={"height": "600px"}
                            ),
                            type="cube"
                        )
                    ], className="graph-container")
                ]),
            ]),
        ], className="main-content"),
        
        # Footer
        html.Footer([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H5("IEEE Dataport Visualization Platform"),
                        html.P("Advanced data visualization tools for exploratory data analysis."),
                    ], md=6),
                    dbc.Col([
                        html.H5("Resources"),
                        html.Ul([
                            html.Li(html.A("Documentation", href="#")),
                            html.Li(html.A("GitHub Repository", href="#")),
                            html.Li(html.A("Report Issues", href="#")),
                        ], className="list-unstyled")
                    ], md=3),
                    dbc.Col([
                        html.H5("Connect"),
                        html.Div([
                            html.I(className="fab fa-github fa-2x me-3"),
                            html.I(className="fab fa-twitter fa-2x me-3"),
                            html.I(className="fab fa-linkedin fa-2x"),
                        ])
                    ], md=3),
                ]),
                html.Hr(),
                html.P("© 2025 IEEE Dataport Visualization Platform. All rights reserved.", className="text-center mt-3")
            ])
        ], className="footer"),
        
        # Store the current chart type
        dcc.Store(id='current-chart-type', data='scatter'),
        
        # Store the dataset info
        dcc.Store(id='dataset-info'),
    ])

app.layout = serve_layout

# Callback for loading data
@app.callback(
    Output('load-data-output', 'children'),
    Output('dataset-info', 'data'),
    Output('x-axis', 'options'),
    Output('x-axis', 'value'),
    Output('y-axis', 'options'),
    Output('y-axis', 'value'),
    Output('key-column', 'options'),
    Output('key-column', 'value'),
    Input('load-data-btn', 'n_clicks'),
    State('bucket-name', 'value'),
    State('data-prefix', 'value'),
    prevent_initial_call=True
)
def load_data(n_clicks, bucket_name, prefix):
    if n_clicks is None:
        return dash.no_update
        
    data = data_service.load_dataset_from_s3(bucket_name, prefix)
    
    if data is None:
        return dbc.Alert("Failed to load data. Please check your credentials and file path.", color="danger"), None, [], None, [], None, [], None
    
    categorical_cols, numerical_cols = data_service.classify_columns()
    
    # Create dropdown options
    cat_options = [{"label": col, "value": col} for col in categorical_cols]
    num_options = [{"label": col, "value": col} for col in numerical_cols]
    
    # Set default values
    cat_value = categorical_cols[0] if categorical_cols else None
    num_value = numerical_cols[0] if numerical_cols else None
    key_value = numerical_cols[1] if len(numerical_cols) > 1 else None
    
    df = data_service.get_dataframe()
    dataset_info = {
        "rows": len(df) if df is not None else 0,
        "columns": len(df.columns) if df is not None else 0,
        "cat_cols": len(categorical_cols),
        "num_cols": len(numerical_cols)
    }
    
    return dbc.Alert(f"Successfully loaded dataset with {dataset_info['rows']} rows and {dataset_info['columns']} columns.", color="success"), dataset_info, cat_options, cat_value, num_options, num_value, num_options, key_value

# Callbacks for toggling chart type buttons
@app.callback(
    Output('current-chart-type', 'data'),
    Output('scatter-btn', 'outline'),
    Output('bar-btn', 'outline'),
    Output('line-btn', 'outline'),
    Input('scatter-btn', 'n_clicks'),
    Input('bar-btn', 'n_clicks'),
    Input('line-btn', 'n_clicks'),
    State('current-chart-type', 'data')
)
def toggle_chart_type(scatter_clicks, bar_clicks, line_clicks, current_chart_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default is scatter plot
        return 'scatter', False, True, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'scatter-btn':
        return 'scatter', False, True, True
    elif button_id == 'bar-btn':
        return 'bar', True, False, True
    elif button_id == 'line-btn':
        return 'line', True, True, False
    
    return current_chart_type, current_chart_type != 'scatter', current_chart_type != 'bar', current_chart_type != 'line'

# Callback to update graph based on selection
@app.callback(
    Output("interactive-graph", "figure"),
    Input("x-axis", "value"),
    Input("y-axis", "value"),
    Input("key-column", "value"),
    Input("current-chart-type", "data"),
    Input("chart-theme", "value")
)
def update_graph(x_col, y_col, key_col, chart_type, theme):
    if not x_col or not y_col:
        return go.Figure().update_layout(
            title="Please select valid X and Y columns",
            template=theme
        )
    
    df = data_service.get_dataframe()
    if df is None:
        return go.Figure().update_layout(
            title="No data available",
            template=theme
        )
    
    # Create base figure based on chart type
    if chart_type == 'scatter':
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col, 
            color=key_col if key_col else None,
            hover_data=df.columns,
            title=f"{y_col} vs {x_col}",
            template=theme,
        )
    elif chart_type == 'bar':
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col, 
            color=key_col if key_col else None,
            hover_data=df.columns,
            title=f"{y_col} by {x_col}",
            template=theme,
        )
    elif chart_type == 'line':
        fig = px.line(
            df, 
            x=x_col, 
            y=y_col, 
            color=key_col if key_col else None,
            hover_data=df.columns,
            title=f"{y_col} Trend by {x_col}",
            template=theme,
        )
    
    # Improve layout
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title=x_col,
        yaxis_title=y_col,
    )
    
    return fig

# Run the app
if __name__ == "__main__":
    app.run(debug=True)