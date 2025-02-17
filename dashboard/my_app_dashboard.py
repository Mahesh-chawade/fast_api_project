import dash
import sqlite3
import pandas as pd
import requests
import calendar
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px

# db_path = r'sqlite:///databases/transactions_info.db'
db_path = r'C:\Users\A200204476\sqlite3\fastApiProject\pythonProject\databases\transactions_info.db'

LOGIN_URL = "http://127.0.0.1:8001/login/"

# Function to get user-specific table names
def get_user_tables(db_path, username):
    conn = sqlite3.connect(db_path)
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)['name'].tolist()
    conn.close()

    # Assuming tables are named like "username_transactions", filter by user
    user_tables = [table for table in tables if username in table]
    return user_tables

# Function to authenticate user and retrieve token
def authenticate_user(username, password):
    response = requests.post(LOGIN_URL, json={"username": username, "password": password})
    if response.status_code == 200:
        return response.json().get("access_token")  # Extract token
    return None

# Function to fetch data for a specific table (no user column filter)
def fetch_data(db_path, table_name):
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {table_name}"  # Get all data from table (no user filtering)
    df = pd.read_sql_query(query, conn)
    conn.close()

    df.columns = [col.lower() for col in df.columns]  # Normalize column names

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    return df

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Bank Transactions Dashboard"

# Layout
app.layout = html.Div([
    dcc.Store(id="logged-in-user", storage_type="session"),  # Store logged-in user info
    dcc.Store(id="auth-token", storage_type="session"),  # Store authentication token

    html.H1("Bank Transactions Overview"),

    # Login Section
    html.Div([
        dcc.Input(id="user", type="text", placeholder="Enter Username", className="inputbox1"),
        dcc.Input(id="password", type="password", placeholder="Enter Password", className="inputbox1"),
        html.Button("Login", id="login-button", n_clicks=0),
        html.Div(id="login-status"),
    ], style={'margin-bottom': '20px'}),

    # Dashboard (Initially hidden)
    html.Div(id="dashboard-content", style={"display": "none"}, children=[
        html.Button('Refresh Data', id='refresh-button', n_clicks=0),
        dcc.Interval(id='interval-component', interval=5000, n_intervals=0),  # Auto-refresh every 5 sec

        html.Label("Select Table:"),
        dcc.Dropdown(
            id='table-selector',
            options=[],  # Dynamically populate this dropdown
            value=None,
            clearable=False
        ),

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
        dcc.Graph(id='income-expense-chart')
    ])
])

# Login Callback
@app.callback(
    [Output("logged-in-user", "data"), Output("auth-token", "data"),
     Output("login-status", "children"), Output("dashboard-content", "style")],
    Input("login-button", "n_clicks"),
    [State("user", "value"), State("password", "value")]
)
def login(n_clicks, username, password):
    if n_clicks > 0:
        token = authenticate_user(username, password)
        if token:
            return username, token, f"Welcome, {username}!", {"display": "block"}  # Show dashboard
        else:
            return None, None, "Invalid username or password. Try again.", {"display": "none"}  # Hide dashboard
    return None, None, "", {"display": "none"}

# Update Table Dropdown
@app.callback(
    Output('table-selector', 'options'),
    Input('logged-in-user', 'data')
)
def update_table_selector(username):
    if not username:
        return []

    user_tables = get_user_tables(db_path, username)  # Get user-specific tables
    return [{'label': table, 'value': table} for table in user_tables]  # Populate dropdown with user-specific tables

# Update Year Filter
@app.callback(
    Output('year-filter', 'options'),
    Output('year-filter', 'value'),
    Input('table-selector', 'value')
)
def update_year_filter(selected_table):
    if not selected_table:
        return [], None

    data = fetch_data(db_path, selected_table)
    if data.empty or 'date' not in data.columns:
        return [], None

    data['year'] = data['date'].dt.year.dropna().astype(int)
    years = sorted(data['year'].unique())
    options = [{'label': str(year), 'value': year} for year in years]

    return options, years[-1] if years else None

# Update Charts
@app.callback(
    [Output('bar-chart', 'figure'), Output('pie-chart', 'figure'), Output('income-expense-chart', 'figure')],
    [Input('table-selector', 'value'), Input('dropdown-column', 'value'), Input('year-filter', 'value'),
     Input('refresh-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State("logged-in-user", "data"), State("auth-token", "data")]
)
def update_charts(selected_table, selected_column, selected_year, n_clicks, n_intervals, username, token):
    if not username or not token or not selected_table:
        return px.bar(title="Please Log In"), px.pie(title="Please Log In"), px.bar(title="Please Log In")

    data = fetch_data(db_path, selected_table)  # Fetch all data (no user filtering)
    if data.empty or 'date' not in data.columns:
        return px.bar(title="No Data Available"), px.pie(title="No Data Available"), px.bar(title="No Data Available")

    # Process data for visualization
    data = data.copy()
    data['year'] = data['date'].dt.year
    data['month'] = data['date'].dt.month
    data['month_name'] = data['month'].apply(lambda x: calendar.month_abbr[x])

    filtered_data = data[data['year'] == selected_year].copy() if selected_year else data.copy()
    if filtered_data.empty:
        return px.bar(title="No Data Available"), px.pie(title="No Data Available"), px.bar(title="No Data Available")

    filtered_data['month_name'] = pd.Categorical(filtered_data['month_name'], categories=calendar.month_abbr[1:], ordered=True)

    # Ensure selected column exists
    if selected_column not in filtered_data.columns:
        selected_column = 'debit' if 'debit' in filtered_data.columns else 'credit'

    agg_data = filtered_data.groupby(['month_name', 'details'], observed=False)[selected_column].sum().reset_index()

    # Bar chart
    bar_fig = px.bar(
        agg_data, x='month_name', y=selected_column, color='details',
        title=f"Monthly {selected_column.capitalize()} Transactions for {selected_year}",
        text_auto=True
    )
    bar_fig.update_layout(xaxis_tickangle=-45)

    # Pie chart
    pie_fig = px.pie(
        filtered_data.groupby('details')[selected_column].sum().reset_index(),
        values=selected_column, names='details',
        title=f"{selected_column.capitalize()} Distribution by Transaction Type",
        hole=0.3
    )

    # Yearly comparison
    yearly_summary = data.groupby('year')[['debit', 'credit']].sum().reset_index().melt(
        id_vars=['year'], value_vars=['debit', 'credit'],
        var_name='Transaction Type', value_name='Amount'
    )
    income_expense_fig = px.bar(yearly_summary, x='year', y='Amount', color='Transaction Type', barmode='group', text_auto=True)

    return bar_fig, pie_fig, income_expense_fig

if __name__ == '__main__':
    app.run_server(debug=True)
