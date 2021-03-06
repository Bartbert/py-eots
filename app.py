import copy
import math
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State, MATCH, ALL
import plotly.graph_objs as go
import pandas as pd
from dash.exceptions import PreventUpdate
from combat_unit import CombatUnit
from battle_analyzer import BattleAnalyzer
from card_analyzer import CardAnalyzer
import enums
import json

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

allied_options = []

for unit in allied_unit_list:
    allied_options.append({"label": unit.unit_name, "value": unit.unit_id})

japan_options = []

for unit in japan_unit_list:
    japan_options.append({"label": unit.unit_name, "value": unit.unit_id})


def plot_expected_winner(df_results):
    df_winner = df_results.groupby(['battle_winner'], as_index=False).agg(winner_count=('battle_winner', 'count'))

    x = df_winner['battle_winner']
    y = df_winner['winner_count'].apply(lambda z: z / 100)

    graph = go.Bar(
        x=x,
        y=y,
        name='Expected Battle Outcome',
        marker=dict(color='lightgreen'),
        text=y.apply(lambda z: '{0:.0f}%'.format(z * 100))
    )

    layout = go.Layout(
        paper_bgcolor='#27293d',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(type='category', title='Battle Winner'),
        yaxis=dict(range=[0, 1], tickformat=".0%", title='Outcome Probability'),
        font=dict(color='white'),
        title='Expected Battle Outcome',
        transition={'duration': 500, 'easing': 'cubic-in-out'},
    )

    return {'data': [graph], 'layout': layout}


def plot_expected_losses(df_results):
    df_losses_allies = df_results.groupby(['allied_damage_applied'], as_index=False).agg(
        damage_count=('allied_damage_applied', 'count'))

    df_losses_allies = df_losses_allies.rename(columns={'allied_damage_applied': 'damage_applied'})
    df_losses_allies['player'] = enums.Player.ALLIES.name

    df_losses_japan = df_results.groupby(['japan_damage_applied'], as_index=False).agg(
        damage_count=('japan_damage_applied', 'count'))

    df_losses_japan = df_losses_japan.rename(columns={'japan_damage_applied': 'damage_applied'})
    df_losses_japan['player'] = enums.Player.JAPAN.name

    df_losses = pd.concat([df_losses_allies, df_losses_japan], ignore_index=True)

    df_pivot = pd.pivot_table(df_losses, index=['player'], columns=['damage_applied'], values=['damage_count'],
                              aggfunc=sum, fill_value=0)

    x_values = []
    for x in df_pivot.columns:
        x_values.append(x[1])

    x_allies = pd.DataFrame(x_values)[0]
    y_allies = pd.DataFrame(df_pivot.values[0])[0].apply(lambda z: z / 100)

    x_japan = pd.DataFrame(x_values)[0]
    y_japan = pd.DataFrame(df_pivot.values[1])[0].apply(lambda z: z / 100)

    graph = [
        go.Bar(
            x=x_allies,
            y=y_allies,
            offsetgroup=0,
            name=enums.Player.ALLIES.name,
            marker=dict(color='lightgreen'),
            text=y_allies.apply(lambda z: '{0:.0f}%'.format(z * 100))
        ),
        go.Bar(
            x=x_japan,
            y=y_japan,
            offsetgroup=1,
            name=enums.Player.JAPAN.name,
            marker=dict(color='lightblue'),
            text=y_japan.apply(lambda z: '{0:.0f}%'.format(z * 100))
        ),
    ]

    layout = go.Layout(
        paper_bgcolor='#27293d',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(type='category', title='Battle Losses'),
        yaxis=dict(range=[0, 1], tickformat=".0%", title='Loss Probability'),
        font=dict(color='white'),
        title='Expected Battle Losses',
        transition={'duration': 500, 'easing': 'cubic-in-out'},
    )

    layout.update(title=dict(x=0.5))

    return go.Figure(
        data=graph,
        layout=layout
    )


def plot_card_analysis(df_results, player: enums.Player):
    x = df_results['attribute']
    y = df_results['probability']

    graph = go.Bar(
        x=x,
        y=y,
        name='Card Attribute Probability',
        marker=dict(color='lightgreen'),
        text=y.apply(lambda z: '{0:.0f}%'.format(z * 100))
    )

    layout = go.Layout(
        paper_bgcolor='#27293d',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(type='category', title='Card Attribute'),
        yaxis=dict(range=[0, 1], tickformat=".0%", title='Probability of Drawing 1+ Cards w/ Attribute'),
        font=dict(color='white'),
        title=f'{player.name} Hand Analysis',
        transition={'duration': 500, 'easing': 'cubic-in-out'},
    )

    return {'data': [graph], 'layout': layout}


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

"""Air/Naval Combat Body Content START"""

allied_ec_mod = html.Div(
    [
        html.P("Allied EC Modifier:", className="m-0"),
        dbc.Input(type="number", min=-2, max=2, step=1, value=0, id="allied-ec-mod"),
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
        dbc.Button("Analyze Battle", id='analyze-battle', color="primary", className="me-1"),
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

body_combat = html.Div(
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
                                html.Div([
                                    dbc.Label("Allied Forces"),
                                ], id='allied-total-cf'),
                                allied_selected_units,
                                html.P(),
                                html.Div(id='allied-forces', children=[]),
                            ], className="p-2 m-2 bg-light border rounded-3 border-primary"),
                            width=6),
                        dbc.Col(html.Div(
                            [
                                html.Div([
                                    dbc.Label("Japan Forces"),
                                ], id='japan-total-cf'),
                                japan_selected_units,
                                html.P(),
                                html.Div(id="japan-forces", children=[]),
                            ], className="p-2 m-2 bg-light border rounded-3 border-primary"),
                            width=6),
                    ]),
                    html.P(),
                    dbc.Row(html.Div([
                        dcc.Graph(id='expected-losses', animate=False,
                                  style={'backgroundColor': '#1a2d46', 'color': '#ffffff'})
                    ])),
                    html.P(),
                    dbc.Row(html.Div([
                        dcc.Graph(id='expected-winner', animate=False,
                                  style={'backgroundColor': '#1a2d46', 'color': '#ffffff'})
                    ])),
                ], className="p-2 bg-light border rounded-3 border-primary"), width=8),
                dbc.Col(html.Div(""), width=1),
            ]
        ),
    ]
)

"""Air/Naval Combat Body END"""

"""Card Analysis Body START"""

acts_username = html.Div(
    [
        dbc.Label("ACTS User Name"),
        dbc.Input(placeholder="Enter your ACTS username...", type="text", id='acts-username'),
    ]
)

acts_password = html.Div(
    [
        dbc.Label("ACTS Password"),
        dbc.Input(placeholder="Enter your ACTS password...", type="password", id='acts-password'),
    ]
)

acts_game_name = html.Div(
    [
        dbc.Label("ACTS EOTS Game Name"),
        dbc.Input(placeholder="Enter the name of your game in ACTS...", type="text", id='acts-game-name'),
    ]
)

allied_hand_size = html.Div(
    [
        html.P("Allied Hand Size:", className="m-0"),
        dbc.Input(type="number", min=3, max=7, step=1, value=7, id="allied-hand-size"),
    ],
)

japan_hand_size = html.Div(
    [
        html.P("Japan Hand Size:", className="m-0"),
        dbc.Input(type="number", min=3, max=7, step=1, value=7, id="japan-hand-size"),
    ],
)

card_deck_type = html.Div(
    [
        dbc.Label("Card Deck"),
        dbc.RadioItems(
            options=[
                {"label": "Full Game Deck", "value": 1},
                {"label": "South Pacific Deck", "value": 2},
            ],
            value=1,
            id="card-deck-type",
        ),
    ]
)

analyze_cards_button = html.Div(
    [
        dbc.Button("Analyze Cards", id='analyze-cards', color="primary", className="me-1"),
    ]
)

body_cards = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Div(), width=1),
                dbc.Col(html.Div([
                    dbc.Row(html.Div([
                        acts_username,
                        html.P(),
                        acts_password,
                        html.P(),
                        acts_game_name,
                        html.P(),
                        card_deck_type,
                        html.P(),
                        allied_hand_size,
                        html.P(),
                        japan_hand_size,
                        html.P(),
                        analyze_cards_button,
                    ],
                        className="p-2 bg-light border rounded-3 border-primary")),
                ]), width=2),
                dbc.Col(html.Div([
                    dbc.Row(html.Div([
                        dcc.Graph(id='allied-probability', animate=False,
                                  style={'backgroundColor': '#1a2d46', 'color': '#ffffff'})
                    ])),
                    html.P(),
                    dbc.Row(html.Div([
                        dcc.Graph(id='japan-probability', animate=False,
                                  style={'backgroundColor': '#1a2d46', 'color': '#ffffff'})
                    ])), ], className="p-2 bg-light border rounded-3 border-primary"), width=8),
                dbc.Col(html.Div(""), width=1),
            ]
        )
    ]
)

"""Card Analysis Body END"""

"""Tabs START"""

tab_combat = dbc.Card(
    dbc.CardBody(
        [
            body_combat
        ]
    )
)

tab_cards = dbc.Card(
    dbc.CardBody(
        [
            body_cards
        ]
    )
)

tabs = dbc.Tabs(
    [
        dbc.Tab(tab_combat, label='Air/Naval Combat'),
        dbc.Tab(tab_cards, label='Card Analysis'),
    ]
)

"""Tabs END"""

"""Final Layout Render"""
app.layout = html.Div([
    navbar,
    tabs,
    dcc.Store(id='allied-combat-force'),
    dcc.Store(id='japan-combat-force')
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
    [Output('allied-forces', 'children'), Output('allied-combat-force', 'data')],
    [Input('allied-selected-units', 'value'), Input('allied-combat-force', 'data')],
    State('allied-forces', 'children')
)
def update_allied_selected_units(value, json_data, children):
    # Determine if there are items in the value list that are not in the allied_combat_force list
    # Any differences need to be added to the UI
    if value:
        ui_indexes = set(value)
    else:
        ui_indexes = set()

    if json_data:
        unit_ids = json.loads(json_data)
    else:
        unit_ids = []

    missing_unit_ids = ui_indexes.difference(set(unit_ids))

    while len(missing_unit_ids) > 0:

        index = missing_unit_ids.pop()
        selected_unit = next((x for x in allied_unit_list if x.unit_id == index), None)

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
                                             disabled=(
                                                 True if math.isnan(selected_unit.move_range_extended) else False)),
                                dbc.Checkbox(id={'type': 'allied-unit-battle-hex', 'index': selected_unit.unit_id},
                                             label='In Battle Hex?', value=selected_unit.is_in_battle_hex),
                                html.P("EC Modifier:", className="m-0"),
                                dbc.Input(id={'type': 'allied-unit-mod', 'index': selected_unit.unit_id},
                                          type='number', min=-2, max=2, step=1, value=0)
                            ]
                        ))
                    ]
                )
            ],
                className='p-1 m-1 bg-light border rounded-3 border-primary',
                id={'type': 'allied-combat-unit', 'index': selected_unit.unit_id},
            )

            children.append(new_element)
            unit_ids.append(selected_unit.unit_id)

    # Determine if there are values in allied_combat_force list that are not in the value list
    # Any differences need to be removed from the UI
    extra_unit_ids = set(unit_ids).difference(ui_indexes)

    while len(extra_unit_ids) > 0:
        unit_id = extra_unit_ids.pop()

        for i in range(len(children)):
            child = children[i]
            index = child['props']['id']['index']

            if index == unit_id:

                for j in range(len(unit_ids)):
                    if unit_ids[j] == unit_id:
                        unit_ids.pop(j)
                        break

                children.pop(i)
                break

    return [children, json.dumps(unit_ids)]


@app.callback(
    [Output('japan-forces', 'children'), Output('japan-combat-force', 'data')],
    [Input('japan-selected-units', 'value'), Input('japan-combat-force', 'data')],
    State('japan-forces', 'children')
)
def update_japan_selected_units(value, json_data, children):
    # Determine if there are items in the value list that are not in the japan_combat_force list
    # Any differences need to be added to the UI
    if value:
        ui_indexes = set(value)
    else:
        ui_indexes = set()

    if json_data:
        unit_ids = json.loads(json_data)
    else:
        unit_ids = []

    missing_unit_ids = ui_indexes.difference(set(unit_ids))

    while len(missing_unit_ids) > 0:

        index = missing_unit_ids.pop()
        selected_unit = next((x for x in japan_unit_list if x.unit_id == index), None)

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
                                             disabled=(
                                                 True if math.isnan(selected_unit.move_range_extended) else False)),
                                dbc.Checkbox(id={'type': 'japan-unit-battle-hex', 'index': selected_unit.unit_id},
                                             label='In Battle Hex?', value=selected_unit.is_in_battle_hex),
                                html.P("EC Modifier:", className="m-0"),
                                dbc.Input(id={'type': 'japan-unit-mod', 'index': selected_unit.unit_id},
                                          type='number', min=-2, max=2, step=1, value=0)
                            ]
                        ))
                    ]
                )
            ],
                className='p-1 m-1 bg-light border rounded-3 border-primary',
                id={'type': 'japan-combat-unit', 'index': selected_unit.unit_id},
            )

            children.append(new_element)
            unit_ids.append(selected_unit.unit_id)

    # Determine if there are values in japan_combat_force list that are not in the value list
    # Any differences need to be removed from the UI
    extra_unit_ids = set(unit_ids).difference(ui_indexes)

    while len(extra_unit_ids) > 0:
        unit_id = extra_unit_ids.pop()

        for i in range(len(children)):
            child = children[i]
            index = child['props']['id']['index']

            if index == unit_id:

                for j in range(len(unit_ids)):
                    if unit_ids[j] == unit_id:
                        unit_ids.pop(j)
                        break

                children.pop(i)
                break

    return [children, json.dumps(unit_ids)]


@app.callback(
    Output({'type': 'allied-image', 'index': MATCH}, 'src'),
    Input({'type': 'allied-unit-flipped', 'index': MATCH}, 'value'),
    State({'type': 'allied-unit-flipped', 'index': MATCH}, 'id'),
)
def toggle_allied_unit_flipped(value, id):
    index = id.get('index')

    if not index:
        raise PreventUpdate

    selected_unit = next((x for x in allied_unit_list if x.unit_id == index), None)

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

    if not index:
        raise PreventUpdate

    selected_unit = next((x for x in allied_unit_list if x.unit_id == index), None)
    selected_unit_copy = copy.deepcopy(selected_unit)

    selected_unit_copy.is_flipped = is_flipped
    selected_unit_copy.is_in_battle_hex = is_battle_hex
    selected_unit_copy.is_extended_range = is_extended
    selected_unit_copy.attack_modifier = modifier

    cf = dbc.Label(f'CF: {selected_unit_copy.combat_factor()}')

    return cf


@app.callback(
    Output('allied-total-cf', 'children'),
    [Input({'type': 'allied-unit-flipped', 'index': ALL}, 'value'),
     Input({'type': 'allied-unit-battle-hex', 'index': ALL}, 'value'),
     Input({'type': 'allied-unit-extended', 'index': ALL}, 'value'),
     Input({'type': 'allied-unit-mod', 'index': ALL}, 'value'),
     Input('allied-combat-force', 'data')]
)
def update_allied_total_cf(is_flipped, is_battle_hex, is_extended, modifier, json_data):
    index_list = json.loads(json_data)
    unit_list = []

    for i in range(len(index_list)):
        index = index_list[i]
        current_unit = next((x for x in allied_unit_list if x.unit_id == index), None)
        current_unit_copy = copy.deepcopy(current_unit)

        current_unit_copy.is_flipped = is_flipped[i]
        current_unit_copy.is_in_battle_hex = is_battle_hex[i]
        current_unit_copy.is_extended_range = is_extended[i]
        current_unit_copy.attack_modifier = modifier[i]

        unit_list.append(current_unit_copy)

    total_cf = sum(map(lambda x: x.combat_factor(), unit_list))

    cf = html.Div([
        dbc.Label(f'Allied Forces', style={'font-weight': 'bold'}),
        dbc.Label(f':  {total_cf} Combat Factors', color='red'),
    ])

    return cf


@app.callback(
    Output({'type': 'japan-image', 'index': MATCH}, 'src'),
    Input({'type': 'japan-unit-flipped', 'index': MATCH}, 'value'),
    State({'type': 'japan-unit-flipped', 'index': MATCH}, 'id'),
)
def toggle_japan_unit_flipped(value, id):
    index = id.get('index')

    selected_unit = next((x for x in japan_unit_list if x.unit_id == index), None)

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

    selected_unit = next((x for x in japan_unit_list if x.unit_id == index), None)
    selected_unit_copy = copy.deepcopy(selected_unit)

    selected_unit_copy.is_flipped = is_flipped
    selected_unit_copy.is_in_battle_hex = is_battle_hex
    selected_unit_copy.is_extended_range = is_extended
    selected_unit_copy.attack_modifier = modifier

    cf = dbc.Label(f'CF: {selected_unit_copy.combat_factor()}')

    return cf


@app.callback(
    Output('japan-total-cf', 'children'),
    [Input({'type': 'japan-unit-flipped', 'index': ALL}, 'value'),
     Input({'type': 'japan-unit-battle-hex', 'index': ALL}, 'value'),
     Input({'type': 'japan-unit-extended', 'index': ALL}, 'value'),
     Input({'type': 'japan-unit-mod', 'index': ALL}, 'value'),
     Input('japan-combat-force', 'data')]
)
def update_japan_total_cf(is_flipped, is_battle_hex, is_extended, modifier, json_data):
    index_list = json.loads(json_data)
    unit_list = []

    for i in range(len(index_list)):
        index = index_list[i]
        current_unit = next((x for x in japan_unit_list if x.unit_id == index), None)
        current_unit_copy = copy.deepcopy(current_unit)

        current_unit_copy.is_flipped = is_flipped[i]
        current_unit_copy.is_in_battle_hex = is_battle_hex[i]
        current_unit_copy.is_extended_range = is_extended[i]
        current_unit_copy.attack_modifier = modifier[i]

        unit_list.append(current_unit_copy)

    total_cf = sum(map(lambda x: x.combat_factor(), unit_list))
    cf = html.Div([
        dbc.Label(f'Japan Forces', style={'font-weight': 'bold'}),
        dbc.Label(f':  {total_cf} Combat Factors', color='red'),
    ])

    return cf


@app.callback(
    [Output('expected-winner', 'figure'), Output('expected-losses', 'figure')],
    [Input('analyze-battle', 'n_clicks'),
     Input('intel-condition', 'value'),
     Input('reaction-player', 'value'),
     Input('air-power-drm', 'value'),
     Input('allied-ec-mod', 'value'),
     Input('japan-ec-mod', 'value')],
    [State({'type': 'allied-unit-flipped', 'index': ALL}, 'value'),
     State({'type': 'allied-unit-battle-hex', 'index': ALL}, 'value'),
     State({'type': 'allied-unit-extended', 'index': ALL}, 'value'),
     State({'type': 'allied-unit-mod', 'index': ALL}, 'value'),
     State('allied-combat-force', 'data'),
     State({'type': 'japan-unit-flipped', 'index': ALL}, 'value'),
     State({'type': 'japan-unit-battle-hex', 'index': ALL}, 'value'),
     State({'type': 'japan-unit-extended', 'index': ALL}, 'value'),
     State({'type': 'japan-unit-mod', 'index': ALL}, 'value'),
     State('japan-combat-force', 'data')]
)
def analyze_battle_results(n_clicks, intel_condition_value, reaction_player_value,
                           air_power_drm_value, allied_ec_mod_value, japan_ec_mod_value,
                           allied_flipped, allied_battle_hex, allied_extended, allied_mod, allied_json,
                           japan_flipped, japan_battle_hex, japan_extended, japan_mod, japan_json):
    if (not n_clicks):
        raise PreventUpdate

    index_list = json.loads(allied_json)

    allied_combat_force = []

    for i in range(len(index_list)):
        index = index_list[i]
        current_unit = next((x for x in allied_unit_list if x.unit_id == index), None)
        current_unit_copy = copy.deepcopy(current_unit)

        current_unit_copy.is_flipped = allied_flipped[i]
        current_unit_copy.is_in_battle_hex = allied_battle_hex[i]
        current_unit_copy.is_extended_range = allied_extended[i]
        current_unit_copy.attack_modifier = allied_mod[i]

        allied_combat_force.append(current_unit_copy)

    index_list = json.loads(japan_json)

    japan_combat_force = []

    for i in range(len(index_list)):
        index = index_list[i]
        current_unit = next((x for x in japan_unit_list if x.unit_id == index), None)
        current_unit_copy = copy.deepcopy(current_unit)

        current_unit_copy.is_flipped = japan_flipped[i]
        current_unit_copy.is_in_battle_hex = japan_battle_hex[i]
        current_unit_copy.is_extended_range = japan_extended[i]
        current_unit_copy.attack_modifier = japan_mod[i]

        japan_combat_force.append(current_unit_copy)

    if (len(allied_combat_force) == 0) | (len(japan_combat_force) == 0):
        raise PreventUpdate

    print(f'Intel Condition: {enums.IntelCondition(intel_condition_value).name}, '
          f'Reaction Player: {enums.Player(reaction_player_value).name}')
    print(f'Allied Force: {allied_json}')
    print(f'Japan Force: {japan_json}')
    print('============================')

    analyzer = BattleAnalyzer(intel_condition=enums.IntelCondition(intel_condition_value),
                              reaction_player=enums.Player(reaction_player_value),
                              air_power_mod=enums.AirPowerModifier(air_power_drm_value),
                              allied_ec_mod=allied_ec_mod_value,
                              japan_ec_mod=japan_ec_mod_value)

    results = analyzer.analyze_battle(allied_combat_force, japan_combat_force)

    winner = plot_expected_winner(results)
    losses = plot_expected_losses(results)

    return [winner, losses]


@app.callback(
    [Output('allied-probability', 'figure'), Output('japan-probability', 'figure')],
    Input('analyze-cards', 'n_clicks'),
    [State('acts-username', 'value'), State('acts-password', 'value'), State('acts-game-name', 'value'),
     State('allied-hand-size', 'value'), State('japan-hand-size', 'value'), State('card-deck-type', 'value')]
)
def analyze_cards(n_clicks, acts_username_value, acts_password_value, acts_game_name_value,
                  allied_hand_size_value, japan_hand_size_value, card_deck_type_value):
    if (not acts_username_value) | (not acts_password_value) | (not acts_game_name_value) | (not n_clicks):
        raise PreventUpdate

    analyzer = CardAnalyzer()

    print(f'Deck Type: {enums.DeckType(card_deck_type_value).name}, '
          f'Allied Hand Size: {allied_hand_size_value}, Japan Hand Size: {japan_hand_size_value}')
    print('======================================')

    results = analyzer.analyze_card_deck(user_name=acts_username_value, pw=acts_password_value,
                                         game_name=acts_game_name_value, deck_type=card_deck_type_value,
                                         allies_draw_count=allied_hand_size_value,
                                         japan_draw_count=japan_hand_size_value)

    allied_plot = plot_card_analysis(df_results=results[0], player=enums.Player.ALLIES)
    japan_plot = plot_card_analysis(df_results=results[1], player=enums.Player.JAPAN)

    return [allied_plot, japan_plot]


if __name__ == '__main__':
    app.run_server(debug=True, port=8888)
