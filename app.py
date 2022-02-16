import copy
import math

import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State, MATCH
import plotly.graph_objs as go
import pandas as pd
from dash.exceptions import PreventUpdate
from combat_unit import CombatUnit
from battle_analyzer import BattleAnalyzer
import enums

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'EOTS'
app._favicon = 'static/images/EnterpriseF.gif'

server = app.server

units = pd.read_csv('data/unit_data.csv')
units['unit_id'] = units.index

an_units = units.loc[units['unit_type'] != 'Ground']

allied_units = an_units.loc[an_units['nationality'] != 'Japan']
japan_units = an_units.loc[an_units['nationality'] == 'Japan']

allied_unit_list = [CombatUnit(**kwargs) for kwargs in allied_units.to_dict(orient='records')]
japan_unit_list = [CombatUnit(**kwargs) for kwargs in japan_units.to_dict(orient='records')]

allied_combat_force = []
japan_combat_force = []

allied_options = []

for unit in allied_unit_list:
    allied_options.append({"label": unit.unit_name, "value": unit.unit_id})

japan_options = []

for unit in japan_unit_list:
    japan_options.append({"label": unit.unit_name, "value": unit.unit_id})

"""Navbar"""
APP_LOGO = "assets/static/images/eots.png"

nav = dbc.Nav(
    [
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem('GMT Game Page',
                                     href='https://www.gmtgames.com/p-880-empire-of-the-sun-4th-printing.aspx',
                                     target='_blank'),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem('Rules',
                                     href='https://gmtwebsiteassets.s3.us-west-2.amazonaws.com/EOTS_Rules-2021-LR.pdf',
                                     target='_blank'),
                dbc.DropdownMenuItem('Mark Herman Designer Website',
                                     href='http://www.members.tripod.com/~MarkHerman/index.html/',
                                     target='_blank')],
            label="Useful Resources",
            nav=True
        )
    ],
    navbar=True)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=APP_LOGO, height="50px")),
                        dbc.Col(dbc.NavbarBrand("Empire of the Sun Battle Analyzer", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                [nav],
                className='ml-auto',
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className='mb-5'
)

"""Navbar END"""

"""Body Content"""

allied_ec_mod = html.Div(
    [
        html.P("Allied EC Modifier:", className="m-0"),
        dbc.Input(type="number", min=-2, max=2, step=1, value=0, id="allied-ed-mod"),
    ],
    id="attacker-sp-count-div",

)

japan_ec_mod = html.Div(
    [
        html.P("Japan EC Modifier:", className="m-0"),
        dbc.Input(type="number", min=-2, max=2, step=1, value=0, id="japan-ec-mod"),
    ],
    id="attacker-leader-mod-div",
)

reaction_player = html.Div(
    [
        dbc.Label("Reaction Player"),
        dbc.RadioItems(
            options=[
                {"label": "Allies", "value": 1},
                {"label": "Japan", "value": 2},
            ],
            value=1,
            id="reaction-player",
        ),
    ]
)

intel_condition = html.Div(
    [
        dbc.Label("Intelligence Condition"),
        dbc.RadioItems(
            options=[
                {"label": "Intercept", "value": 0},
                {"label": "Surprise", "value": 3},
                {"label": "Ambush", "value": 4},
            ],
            value=0,
            id="intel-condition",
        ),
    ]
)

air_power_drm = html.Div(
    [
        dbc.Label("Allied Air Power DRM"),
        dbc.RadioItems(
            options=[
                {"label": "+0 (1942)", "value": 0},
                {"label": "+1 (1943)", "value": 1},
                {"label": "+3 (1944/1945)", "value": 3},
            ],
            value=0,
            id="air-power-drm",
        ),
    ]
)

analyze_button = html.Div(
    [
        dbc.Button("Analyze Battle", color="primary", className="me-1"),
    ]
)

allied_selected_units = html.Div(
    [
        dcc.Dropdown(id="allied-selected-units", multi=True, options=allied_options, className="dash-bootstrap"),
    ]
)

japan_selected_units = html.Div(
    [
        dcc.Dropdown(id="japan-selected-units", multi=True, options=japan_options, className="dash-bootstrap")
    ]
)

body = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div(), width=1),
                dbc.Col(html.Div([
                    dbc.Row(html.Div([
                        reaction_player,
                        html.P(),
                        intel_condition,
                        html.P(),
                        air_power_drm,
                        html.P(),
                        allied_ec_mod,
                        html.P(),
                        japan_ec_mod,
                        html.P(),
                        analyze_button,
                    ],
                        className="p-2 bg-light border rounded-3 border-primary")),
                ]), width=2),
                dbc.Col(html.Div([
                    dbc.Row([
                        dbc.Col(html.Div(
                            [
                                dbc.Label("Allied Forces"),
                                allied_selected_units,
                                html.P(),
                                html.Div(id='allied-forces', children=[]),
                            ], className="p-2 m-2 bg-light border rounded-3 border-primary"),
                            width=6),
                        dbc.Col(html.Div(
                            [
                                dbc.Label("Japan Forces"),
                                japan_selected_units,
                                html.P(),
                                html.Div(id="japan-forces", children=[]),
                            ], className="p-2 m-2 bg-light border rounded-3 border-primary"),
                            width=6),
                    ]),
                    html.P(),
                    dbc.Row(html.Div([
                        dcc.Graph(id='expected-winner', animate=True,
                                  style={'backgroundColor': '#1a2d46', 'color': '#ffffff'})
                    ])),
                    html.P(),
                    dbc.Row(html.Div([
                        dcc.Graph(id='expected-losses', animate=False,
                                  style={'backgroundColor': '#1a2d46', 'color': '#ffffff'})
                    ])),
                ], className="p-2 bg-light border rounded-3 border-primary"), width=8),
                dbc.Col(html.Div(""), width=1),
            ]
        ),
    ]
)

"""Body End"""

"""Final Layout Render"""
app.layout = html.Div([
    navbar, body
])


# Navbar
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output('allied-forces', 'children'),
    Input('allied-selected-units', 'value'),
    State('allied-forces', 'children')
)
def update_allied_selected_units(value, children):
    if value:
        index = len(value) - 1
        selected_unit = next((x for x in allied_unit_list if x.unit_id == value[index]), None)
    else:
        raise PreventUpdate

    if selected_unit:
        new_element = html.Div(children=
        [
            dbc.Row(
                [
                    dbc.Col(width=4, children=html.Div(
                        [
                            html.Img(id={'type': 'allied-image', 'index': selected_unit.unit_id},
                                     src=f'assets/static/images/{selected_unit.image_name_front}'),
                            html.P(),
                            html.Div([
                                dbc.Label(f'CF: {selected_unit.combat_factor()}'),
                            ],
                                id={'type': 'allied-cf', 'index': selected_unit.unit_id}
                            ),
                        ]
                    )),
                    dbc.Col(width=8, children=html.Div(
                        [
                            dbc.Checkbox(id={'type': 'allied-unit-flipped', 'index': selected_unit.unit_id},
                                         label='Flipped?', value=False),
                            dbc.Checkbox(id={'type': 'allied-unit-extended', 'index': selected_unit.unit_id},
                                         label='Extended Range?', value=False,
                                         disabled=(True if math.isnan(selected_unit.move_range_extended) else False)),
                            dbc.Checkbox(id={'type': 'allied-unit-battle-hex', 'index': selected_unit.unit_id},
                                         label='In Battle Hex?', value=selected_unit.is_in_battle_hex),
                            dbc.Input(id={'type': 'allied-unit-mod', 'index': selected_unit.unit_id},
                                      type='number', min=-2, max=2, step=1, value=0)
                        ]
                    ))
                ]
            )
        ],
            className='p-1 m-1 bg-light border rounded-3 border-primary'
        )

        children.append(new_element)
        allied_combat_force.append(copy.deepcopy(selected_unit))

    return children


@app.callback(
    Output('japan-forces', 'children'),
    Input('japan-selected-units', 'value'),
    State('japan-forces', 'children')
)
def update_japan_selected_units(value, children):
    if value:
        index = len(value) - 1
        selected_unit = next((x for x in japan_unit_list if x.unit_id == value[index]), None)
    else:
        raise PreventUpdate

    if selected_unit:
        new_element = html.Div(children=
        [
            dbc.Row(
                [
                    dbc.Col(width=4, children=html.Div(
                        [
                            html.Img(id={'type': 'japan-image', 'index': selected_unit.unit_id},
                                     src=f'assets/static/images/{selected_unit.image_name_front}'),
                            html.P(),
                            html.Div([
                                dbc.Label(f'CF: {selected_unit.combat_factor()}'),
                            ],
                                id={'type': 'japan-cf', 'index': selected_unit.unit_id}
                            ),
                        ]
                    )),
                    dbc.Col(width=8, children=html.Div(
                        [
                            dbc.Checkbox(id={'type': 'japan-unit-flipped', 'index': selected_unit.unit_id},
                                         label='Flipped?', value=False),
                            dbc.Checkbox(id={'type': 'japan-unit-extended', 'index': selected_unit.unit_id},
                                         label='Extended Range?', value=False,
                                         disabled=(True if math.isnan(selected_unit.move_range_extended) else False)),
                            dbc.Checkbox(id={'type': 'japan-unit-battle-hex', 'index': selected_unit.unit_id},
                                         label='In Battle Hex?', value=selected_unit.is_in_battle_hex),
                            dbc.Input(id={'type': 'japan-unit-mod', 'index': selected_unit.unit_id},
                                      type='number', min=-2, max=2, step=1, value=0)
                        ]
                    ))
                ]
            )
        ],
            className='p-1 m-1 bg-light border rounded-3 border-primary'
        )

        children.append(new_element)
        japan_combat_force.append(copy.deepcopy(selected_unit))

    return children


@app.callback(
    Output({'type': 'allied-image', 'index': MATCH}, 'src'),
    Input({'type': 'allied-unit-flipped', 'index': MATCH}, 'value'),
    State({'type': 'allied-unit-flipped', 'index': MATCH}, 'id'),
)
def toggle_allied_unit_flipped(value, id):
    index = id.get('index')

    selected_unit = next((x for x in allied_combat_force if x.unit_id == index), None)
    selected_unit.is_flipped = value

    if value:
        src = f'assets/static/images/{selected_unit.image_name_back}'
    else:
        src = f'assets/static/images/{selected_unit.image_name_front}'

    return src


@app.callback(
    Output({'type': 'allied-cf', 'index': MATCH}, 'children'),
    [Input({'type': 'allied-unit-flipped', 'index': MATCH}, 'value'),
     Input({'type': 'allied-unit-battle-hex', 'index': MATCH}, 'value'),
     Input({'type': 'allied-unit-extended', 'index': MATCH}, 'value'),
     Input({'type': 'allied-unit-mod', 'index': MATCH}, 'value')],
    State({'type': 'allied-unit-flipped', 'index': MATCH}, 'id'),
)
def update_allied_unit_cf(is_flipped, is_battle_hex, is_extended, modifier, is_flipped_id):
    index = is_flipped_id.get('index')

    selected_unit = next((x for x in allied_combat_force if x.unit_id == index), None)
    selected_unit.is_flipped = is_flipped
    selected_unit.is_in_battle_hex = is_battle_hex
    selected_unit.is_extended_range = is_extended
    selected_unit.attack_modifier = modifier

    cf = dbc.Label(f'CF: {selected_unit.combat_factor()}')

    return cf


@app.callback(
    Output({'type': 'japan-image', 'index': MATCH}, 'src'),
    Input({'type': 'japan-unit-flipped', 'index': MATCH}, 'value'),
    State({'type': 'japan-unit-flipped', 'index': MATCH}, 'id'),
)
def toggle_japan_unit_flipped(value, id):
    index = id.get('index')

    selected_unit = next((x for x in japan_combat_force if x.unit_id == index), None)
    selected_unit.is_flipped = value

    if value:
        src = f'assets/static/images/{selected_unit.image_name_back}'
    else:
        src = f'assets/static/images/{selected_unit.image_name_front}'

    return src


@app.callback(
    Output({'type': 'japan-cf', 'index': MATCH}, 'children'),
    [Input({'type': 'japan-unit-flipped', 'index': MATCH}, 'value'),
     Input({'type': 'japan-unit-battle-hex', 'index': MATCH}, 'value'),
     Input({'type': 'japan-unit-extended', 'index': MATCH}, 'value'),
     Input({'type': 'japan-unit-mod', 'index': MATCH}, 'value')],
    State({'type': 'japan-unit-flipped', 'index': MATCH}, 'id'),
)
def update_japan_unit_cf(is_flipped, is_battle_hex, is_extended, modifier, is_flipped_id):
    index = is_flipped_id.get('index')

    selected_unit = next((x for x in japan_combat_force if x.unit_id == index), None)
    selected_unit.is_flipped = is_flipped
    selected_unit.is_in_battle_hex = is_battle_hex
    selected_unit.is_extended_range = is_extended
    selected_unit.attack_modifier = modifier

    cf = dbc.Label(f'CF: {selected_unit.combat_factor()}')

    return cf


if __name__ == '__main__':
    app.run_server(debug=True, port=8888)
