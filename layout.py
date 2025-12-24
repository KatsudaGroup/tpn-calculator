import dash
import dash_bootstrap_components as dbc
from dash import dash_table
from dash import dcc, html
from dash.dash_table.Format import Format

CONTENT_STYLE = {
    "marginLeft":  "2rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}

detailed_setting_id_type = "detailed_settings"

def layout_upload_section():
    layout = html.Div(
        [
            html.H3("1. Import Data"),
            dbc.Alert([
                "Import Simple Western data exported from Compass. TSV (.tsv), CSV (.csv), and Excel (.xlsx, .xls) files are supported.",
                html.Br(),
                "Your data are stored in the user's browser (local storage).",
                "The server does not retain your files.",
            ], color = "primary"),
            dcc.Upload(
                id='upload_data',
                children=html.Div(['Drag & drop or ', html.A('click to select'), ' your Simple Western data file. ']),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False,
                accept=".txt,.tsv,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel",
            ),
            html.P(id='uploaded_filename', style={'whiteSpace': 'pre-line'}),
        ]
    )
    return layout

def layout_edit_lane():
    layout = html.Div(
        [
            html.H3("2. Select Drawing Mode"),
            html.Label("Drawing Mode"),
            dbc.RadioItems(
                options = [
                    {"label": "As-is (raw) data", "value": "as_is"},  
                    {"label": "Normalized by total protein. (requires prior normalization.)", "value": "normalized_new"},
                ],
                value = "as_is",
                id = "draw_type_radio",
            ),
            html.Br(),
            dbc.Collapse(
                children = [
                    dbc.Card([
                        dbc.CardHeader('Lane Order'),
                        dbc.CardBody([
                            dbc.Alert([
                                "1) Set lane order using the dropdowns in the table.",
                                html.Br(),
                                "2) Click 'Generate' at the bottom of the page.",
                            ], color = 'primary'),
                            html.Br(),
                            dbc.ButtonGroup([
                                dbc.Button("Reset", id = "lane_reset_button", outline = True, color="primary"),
                                dbc.Button("Clear", id = "lane_clear_button", outline = True, color="primary"),
                            ], class_name="me-1 mb-3"),
                            dbc.ButtonGroup([
                                dbc.Button('Add lane', id = "add_lane_button", outline = True, color = "primary"),
                                dbc.Button("Insert above selected", id = "lane_insert_button", outline = True, color = "primary",),
                            ], className="mb-3"),
                            dash_table.DataTable(
                                id = "asis_lane_setting_table",
                                columns = [{"id": 'sample_name', 'name': 'Sample', 
                                            'editable': True, 'presentation': 'dropdown' },
                                            {"id": "label", "name": "Custom Label", 
                                             "editable": True, "presentation": "input"}],
                                row_deletable = True,
                                row_selectable = "single",
                                style_cell = {'textAlign': 'left'},
                                style_as_list_view = True,
                                css=[{"selector":".dropdown", "rule": "position: static"}],
                            ),
                            dbc.Tooltip("Restore the default lane order.", target="lane_reset_button"),
                            dbc.Tooltip("Clear all rows in the table.", target="lane_clear_button"),
                            dbc.Tooltip("Append a new lane at the bottom.", target="add_lane_button"),
                            dbc.Tooltip("Insert a new lane above the selected row.", target="lane_insert_button"),
                        ])
                    ]),
                ],
                id = "asis_collapse",
            ),
            html.Br(),
            dcc.ConfirmDialog(
                id = "set_total_lane_confirm",
            ),
        ]
    )
    return layout

def layout_draw_options(default_value):
    layout = html.Div(
        [
            html.H3("3. Set Draw Options"),
            html.H5("Signal Upper Bound"),
            dcc.Slider(min = 0, max = 100000, step = None, value = 10000, id = "signal_limit_slider", 
                       tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),

            html.H5("Molecular Weight Range"),
            dbc.InputGroup([
                dbc.InputGroupText("Set range by molecular weight"),
                dbc.InputGroupText([
                    dbc.Switch(id = "draw_mw_range_switch", value = False),
                ]),
                dbc.InputGroupText(" Min(kDa)"),
                dbc.Input(id = "draw_mw_range_min", type="number", value = 20, persistence='local'),
                dbc.InputGroupText(" Max(kDa)"),
                dbc.Input(id = "draw_mw_range_max", type="number", value = 230, persistence='local'),
            ],className = "mb-3"),

            html.H5("Molecular Weight Markers"),
            dbc.Checklist(
                options = [
                    {"label": "Show marker indicators", "value": "add_marker_line"},
                    {"label": "Show MW labels",   "value": "add_mw_labels"},
                ],
                id = "marker_switch", switch = True, value = ["add_marker_line, add_mw_labels"]
            ),
            dbc.InputGroup([
                dbc.InputGroupText("Marker positions (kDa)"),
                dbc.Input(id = "marker_mw_input", placeholder = 'e.g. 230, 180, 116[beta-gal], 66[BSA], 40, 12'),
            ]),
            dbc.Tooltip(
                "Enter molecular weights separated by commas. "
                "If a label is specified in [brackets], the label will be shown instead of the number. "
                "Example: 230, 180, 116[B-gal], 66[BSA], 40, 12",
                target="marker_mw_input",
            ),
            #dbc.Tooltip("Short horizontal lines drawn on the image to indicate the specified molecular weights.", target="add_marker_line"),
            #dbc.Tooltip("Numerical molecular weight labels displayed next to each indicator.", target="add_mw_labels"),
            html.Br(),

            html.H5("Lane Labels"),
            dbc.RadioItems(
                id = "lane_label_select", value = None,
                options = [
                    {"label": "None", "value" : None},
                    {"label": "Lane Number", "value": "lane_number"},
                    {"label": "Sample Name", "value": "sample_name"},
                    {"label": "Custom", "value": "user_defined"},
                ],
            ),
            dbc.Switch(id = "lane_label_rotate_switch", label = "Rotate Labels 90°", value = False),
            html.Br(),

            html.H5("Detailed Settings"),
            dbc.Collapse(
                children=[
                    dbc.InputGroup([
                        dbc.InputGroupText("Margins (px)"),
                        dbc.InputGroupText(
                            dbc.Switch(
                                value = False, 
                                id = {"type": detailed_setting_id_type, 'key': "offset_switch"}
                            ),
                        ),
                        dbc.InputGroupText("Top"),
                        dbc.Input(
                            value = default_value["offset_top"], type="number",
                            id = {"type": detailed_setting_id_type, 'key': "offset_top"}
                        ),
                        dbc.InputGroupText("Bottom"),
                        dbc.Input(
                            value = default_value["offset_bottom"], type="number",
                            id = {"type": detailed_setting_id_type, 'key': "offset_bottom"}
                        ),
                        dbc.InputGroupText("Left"),
                        dbc.Input(
                            value = default_value["offset_left"], type="number",
                            id = {"type": detailed_setting_id_type, 'key': "offset_left"}
                        ),
                        dbc.InputGroupText("Right"),
                        dbc.Input(
                            value = default_value["offset_right"], type="number",
                            id = {"type": detailed_setting_id_type, 'key': "offset_right"}
                        ),
                        dbc.Button("Restore Defaults", id = "offset_default_button"),
                    ], className="mb-3"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Band Width & Spacing (px)"),
                        dbc.InputGroupText(
                            dbc.Switch(
                                value = False, 
                                id = {"type": detailed_setting_id_type, 'key': "band_width_switch"}
                            )
                        ),
                        dbc.InputGroupText("Band Width"),
                        dbc.Input(
                            value = default_value["band_width"], type="number", 
                            id = {"type": detailed_setting_id_type, 'key': "band_width"}
                        ),
                        dbc.InputGroupText("Band Spacing"),
                        dbc.Input(
                            value = default_value["band_spacing"], type="number", 
                            id = {"type": detailed_setting_id_type, 'key': "band_spacing"},
                        ),
                        dbc.Button("Restore Defaults", id = "band_width_default_button"),
                    ], className="mb-3"),
                    dbc.InputGroup([
                        dbc.InputGroupText("Label Font Size (pt)"),
                        dbc.InputGroupText(
                            dbc.Switch(
                                value = False,
                                id = {"type": detailed_setting_id_type, 'key': "label_font_size_switch"}
                            ),
                        ),
                        dbc.InputGroupText("Lane Label Size"),
                        dbc.Input(
                            value = default_value["lane_label_size"], type="number", 
                            id = {"type": detailed_setting_id_type, 'key': "lane_label_size"}
                        ),
                        dbc.InputGroupText("Molecular Weight Label Size"),
                        dbc.Input(
                            value = default_value["mw_label_size"], type="number", 
                            id = {"type": detailed_setting_id_type, 'key': "mw_label_size"}
                        ),
                        dbc.Button("Restore Defaults", id = "label_size_default_button")
                    ], className="mb-3"),
                ],
                is_open= True,
                id = "detailed_settings_collapse",
            )
        ]
    )
    return layout

def layout_generate_image():
    layout = html.Div(
        [
            html.H3("4. Generate Image"),
            dbc.Button('Generate', id = 'generate_button', disabled = True, className="me-1"),
            dbc.ButtonGroup([
                dbc.Button('Download Image', id = 'download_button', disabled = True, className="", outline = False, color='secondary'),
                dbc.Button("Download Log", id = "download_log_button", disabled = True, className="", outline = False, color = 'secondary'),
                dbc.Button("Download Both", id = "download_all_button", disabled = True, className="", outline = False, color = 'secondary'),
            ]),
            html.P(id = 'generate_message'),

            html.Br(),
            html.Img(id = 'resulted_image'),
            dbc.Textarea(id = "generate_log", readonly = True),
            html.Br(),
            dcc.Download(id = 'download_image'),
            dcc.Download(id = 'download_log'),
            dcc.Download(id = 'download_all'),
        ]
    )
    return layout


def layout_control_panel(default_value):
    layout = [ 
        layout_upload_section(),
        layout_edit_lane(),
        layout_draw_options(default_value),
        layout_generate_image(),
    ]
    return layout

def layout_normalization_panel():
    layout = [
        html.Div([
            html.H5("Series Mapping for Normalization"),
            dbc.Alert([
                "For normalization based on total protein intensity, please specify the following information for each signal series:",
                html.Ol([
                    html.Li([
                        "Specify whether each series represents a ", html.Em("total protein"), " or a ", html.Em("target protein"),
                        " (in the “Type” column)."
                    ]),
                    html.Li([
                        "For each ", html.Em("target protein"), " series, select the corresponding ", html.Em("total protein"),
                        " series used as its reference (in the “Associated Series” column). ",
                        html.Strong("If a target series does not have an associated series, it will remain unnormalized and output as raw intensity.")
                    ]),
                ]),
            ], color = "primary"),
            dbc.Button("Reset Table", id="lane_relationship_table_reset_button", outline = True, color="primary", class_name="mb-3"),
            dash_table.DataTable(
                id="lane_relationship_table",
                columns = [
                    {'id': 'index', 'name': '#'},
                    {'id': "sample_name", 'name': "Series Name"},
                    {'id': "type", 'name': "Type", 'editable': True, 'presentation': "dropdown"},
                    {'id': "associated_lane", 'name': "Associated Series", 'editable': True, 'presentation': "dropdown"},
                ],
                style_cell = {'textAlign': 'left'},
                style_as_list_view = True,
                css=[{"selector":".dropdown", "rule": "position: static"}],
                #row_selectable="multi",
                cell_selectable = False,
                dropdown = {
                    'type': {
                        "options": [{'value': x, 'label': x} for x in ['Target', 'Total']],
                        'clearable': False
                    }
                },
                style_data_conditional = [
                    {
                        'if': {'column_id': 'associated_lane', 'filter_query': '{type} = "Total"'},
                        'backgroundColor': '#e0e0e0',
                        'color': '#a0a0a0'
                    },
                ],
            ),
            html.Br(),

            dbc.Accordion([
                dbc.AccordionItem([
                    dbc.Alert([
                        "You can annotate series in batch by specifying their indices and ranges (e.g., 1,2,3,4 or 1-4).",
                        html.Br(),
                        "Specify the indices for ", html.Em("Total Protein"), " series. Optionally, specify ", html.Em("Target Protein"), " series as well.",
                        html.Br(),
                        "If both Target and Total are provided, they are paired in order: (Target 1 ↔ Total 1), (Target 2 ↔ Total 2), ...",
                        html.Br(),
                        "If Target is left empty, only the specified ", html.Em("Total Protein"), " series will be labeled as “Total”."
                    ], color='primary'),
                    dbc.Form(
                        dbc.Row([
                            dbc.Label("(Optional) Target Protein Series", width="auto"),
                            dbc.Col(dbc.Input(id="target_lane_specifier", type="text", placeholder = "1-4,6,8-10"), className="me-3"),
                            dbc.Label("Total Protein Series", width="auto"),
                            dbc.Col(dbc.Input(id="total_lane_specifier", type="text", placeholder = "1-4,6,8-10"),className="me-3"),
                            dbc.Col(dbc.Button("Apply", id = "set_relationship_by_specifier_button", className="mb-3")),
                        ],
                        className="g-2")
                    ),
                    html.P(id = "expand_display_p"),
                ],
                title = "Batch Annotation")
            ], className="mb-3"),
        ]),
        html.H5("Normalization Calculation"),
        dbc.InputGroup([
            dbc.InputGroupText("Normalize to (Total Protein Series)"),
            dbc.Select(id = "normalization_target_dropdown"),
        ], className="mb-3"),

        dbc.InputGroup([
            dbc.InputGroupText("Signal Integration Range"),
            dbc.InputGroupText([
                dbc.Switch(id = "signal_calculation_range_switch", value = False),
            ]),
            dbc.InputGroupText(" Min(kDa)"),
            dbc.Input(id = "signal_calculation_range_min", type="number", value = 20, persistence='local'),
            dbc.InputGroupText(" Max(kDa)"),
            dbc.Input(id = "signal_calculation_range_max", type="number", value = 230, persistence='local'),
        ],className = "mb-3"),

        dbc.InputGroup([
            dbc.InputGroupText([
                #"Stop signal summation when a negative value appears ",
                "Stop integration at first negative value (from high to low MW)",
            ]),
            dbc.InputGroupText([
                dbc.Switch(id = "stop_summation_negative_value", value = False),
            ])
        ], className="mb-3"),

        dbc.Button("Compute Normalized Signals", 
                   id = "calculate_normalized_signal_button", className="mb-3"),

        html.H5("Normalization Summary"),
        dash_table.DataTable(
            id="normalization_result_table",
            columns = [
                {"id": "sample_name", "name": "Series Name"},
                {"id": "raw_total_signal", "name": "Raw Total Intensity"},
                {"id": "factor", "name": "Normalization Factor"},
                {"id": "note", "name": "Note"},
            ]
        ),

    ]
    return layout

def layout_rawdata_panel():
    layout = [
        dash_table.DataTable(
            id = "raw_data_table",
            cell_selectable = False,
        )
    ]
    return layout


def layout_graph_panel():
    layout = [
        html.H5("Plot of Raw Data"),
        dcc.Graph(id = "graph"),
        html.H5("Plot of Normalized Data"),
        dcc.Graph(id = "graph_normalized"),
    ]
    return layout

def layout_normalized_data_panel():
    layout = [
        dash_table.DataTable(
            id = "normalized_data_table",
            cell_selectable = False,
            export_format = 'xlsx',
        )
    ]
    return layout

def layout_link():
    import os
    docs_url = os.getenv("TPN_CALCULATOR_DOCS_URL")
    repo_url = os.getenv("TPN_CALCULATOR_REPO_URL")
    links = []
    if docs_url:
        links.append(html.A("Documentation", href = docs_url, target="_blank"))
    if docs_url and repo_url:
        links.append(" | ")
    if repo_url:
        links.append(html.A("Repository", href = repo_url, target="_blank"))
    return html.Div(links) if links else None

def app_layout(default_value):
    layout = html.Div(
        [
            html.H1("TPN Calculator"),
            html.P('A web-based tool for total protein normalization and virtual lane visualization of Simple Western data'),
            layout_link(),
            dbc.Tabs(
                [
                    dbc.Tab(layout_control_panel(default_value), label = "Main", style = CONTENT_STYLE),
                    dbc.Tab(layout_rawdata_panel(), label = "Raw Data", style = CONTENT_STYLE),
                    dbc.Tab(layout_normalization_panel(), label = "Normalization", style = CONTENT_STYLE),
                    dbc.Tab(layout_normalized_data_panel(), label = "Normalized Data", style = CONTENT_STYLE),
                    dbc.Tab(layout_graph_panel(), label = 'Line Plot', style = CONTENT_STYLE),
                ],
            ),
            dcc.Store('store_total_protein_lane_id'),
            dcc.Store('store_lane_signal_sum_list'),
            dcc.Store('store_normalize_factor'),
            dcc.Store('store_fileinfo'),
        ],
        style = CONTENT_STYLE

    )
    return layout
