import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'EOTS'
app._favicon = 'static/images/EnterpriseF.gif'

server = app.server

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

"""Final Layout Render"""
app.layout = html.Div([
    navbar
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


if __name__ == '__main__':
    app.run_server(debug=True, port=8888)
