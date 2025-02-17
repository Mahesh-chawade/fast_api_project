import dash
import sqlite3
import pandas as pd
import requests
import calendar
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px

# Database Path
db_path = r'C:\Users\A200204476\sqlite3\fastApiProject\pythonProject\databases\transactions_info.db'
LOGIN_URL = "http://127.0.0.1:8001/login/"

# Authenticate User
def authenticate_user(username, password):
    response = requests.post(LOGIN_URL, json={"username": username, "password": password})
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

# Fetch User-Specific Tables
def get_user_tables(db_path, username):
    conn = sqlite3.connect(db_path)
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)['name'].tolist()
    conn.close()
    return [table for table in tables if username in table]

# Fetch Data from Table
def fetch_data(db_path, table_name):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    df.columns = [col.lower() for col in df.columns]
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

# Initialize Dash App
app = dash.Dash(__name__)
app.title = "Bank Transactions Dashboard"

# Layout
app.layout = html.Div([
    dcc.Store(id="logged-in-user", storage_type="session"),
    dcc.Store(id="auth-token", storage_type="session"),

    html.H1("Bank Transactions Overview"),
    html.Div([
        dcc.Input(id="user", type="text", placeholder="Enter Username"),
        dcc.Input(id="password", type="password", placeholder="Enter Password"),
        html.Button("Login", id="login-button", n_clicks=0),
        html.Div(id="login-status"),
    ], style={'margin-bottom': '20px'}),

    html.Div(id="dashboard-content", style={"display": "none"}, children=[
        html.Button('Refresh Data', id='refresh-button', n_clicks=0),
        dcc.Interval(id='interval-component', interval=5000, n_intervals=0),

        html.Label("Select Table:"),
        dcc.Dropdown(id='table-selector', options=[], value=None, clearable=False),

        html.Label("Select Transaction Type:"),
        dcc.Dropdown(
            id='dropdown-column',
            options=[
                {'label': 'Debit Amount', 'value': 'debit'},
                {'label': 'Credit Amount', 'value': 'credit'},
                {'label': 'Balance Amount', 'value': 'balance'}
            ],
            value='debit',
            clearable=False
        ),

        html.Label("Select Year:"),
        dcc.Dropdown(id='year-filter', clearable=False),

        dcc.Graph(id='bar-chart'),
        dcc.Graph(id='pie-chart'),
        html.H2("Income vs. Expenses Yearly Comparison"),
        dcc.Graph(id='income-expense-chart'),
        html.H2("Box Plot"),
        dcc.Graph(id='box-plot')
    ])
])

# Login Callback
@app.callback(
    [Output("logged-in-user", "data"), Output("auth-token", "data"), Output("login-status", "children"), Output("dashboard-content", "style")],
    [Input("login-button", "n_clicks")],
    [State("user", "value"), State("password", "value")]
)
def login(n_clicks, username, password):
    if n_clicks > 0 and username and password:
        token = authenticate_user(username, password)
        if token:
            return username, token, "Login Successful", {"display": "block"}
    return None, None, "Invalid Credentials", {"display": "none"}

# Update Charts
@app.callback(
    [Output('bar-chart', 'figure'), Output('pie-chart', 'figure'), Output('income-expense-chart', 'figure'), Output('box-plot', 'figure')],
    [Input('table-selector', 'value'), Input('dropdown-column', 'value'), Input('year-filter', 'value'),
     Input('refresh-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State("logged-in-user", "data"), State("auth-token", "data")]
)
def update_charts(selected_table, selected_column, selected_year, n_clicks, n_intervals, username, token):
    if not username or not token or not selected_table:
        return px.bar(title="Please Log In"), px.pie(title="Please Log In"), px.bar(title="Please Log In"), px.box(title="Please Log In")

    data = fetch_data(db_path, selected_table)
    if data.empty or 'date' not in data.columns:
        return px.bar(title="No Data Available"), px.pie(title="No Data Available"), px.bar(title="No Data Available"), px.box(title="No Data Available")

    data['year'] = data['date'].dt.year
    data['month'] = data['date'].dt.month
    data['month_name'] = data['month'].apply(lambda x: calendar.month_abbr[x])

    filtered_data = data[data['year'] == selected_year] if selected_year else data
    if filtered_data.empty:
        return px.bar(title="No Data Available"), px.pie(title="No Data Available"), px.bar(title="No Data Available"), px.box(title="No Data Available")

    bar_fig = px.bar(filtered_data, x='month_name', y=selected_column, color='details', text_auto=True)
    pie_fig = px.pie(filtered_data, values=selected_column, names='details', hole=0.3)
    income_expense_fig = px.bar(filtered_data, x='year', y=selected_column, color='details', barmode='group', text_auto=True)
    box_fig = px.box(filtered_data, y=selected_column)

    return bar_fig, pie_fig, income_expense_fig, box_fig

if __name__ == '__main__':
    app.run_server(debug=True)