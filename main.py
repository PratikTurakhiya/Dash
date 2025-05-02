import os
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Load Excel data
df = pd.read_excel("Juice_Sales_Data.xlsx")
df["Date"] = pd.to_datetime(df["Date"])

# Extract week and weekday columns for filtering and grouping
df['Week'] = df['Date'].dt.to_period('W').dt.start_time
df['Weekday'] = df['Date'].dt.day_name()

# Initialize Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
app.title = "Juice Sales Dashboard"

# App layout
app.layout = dbc.Container([
    html.H1("Juice Sales Dashboard", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=df["Date"].min(),
                max_date_allowed=df["Date"].max(),
                start_date=df["Date"].min(),
                end_date=df["Date"].max(),
                style={'marginBottom': '10px'}
            ),
        ], width=6),
    ]),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Total Sales"),
            dbc.CardBody(html.H3(id="total-sales", className="card-title"))
        ], color="success", inverse=True), width=4),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Cash Sales"),
            dbc.CardBody(html.H4(id="cash-sales", className="card-title"))
        ], color="info", inverse=True), width=4),

        dbc.Col(dbc.Card([
            dbc.CardHeader("Online Sales"),
            dbc.CardBody(html.H4(id="online-sales", className="card-title"))
        ], color="primary", inverse=True), width=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='sales-line'), width=8),
        dbc.Col(dcc.Graph(id='payment-pie'), width=4)
    ]),

    dbc.Row([
        dbc.Col(html.H5("Highest Sales Day of the Week"), width=12),
        dbc.Col(html.H6(id="highest-day"), width=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.H5("Average Daily Sales"), width=12),
        dbc.Col(html.H6(id="avg-sales"), width=12),
    ])
], fluid=True)

@app.callback(
    [Output('sales-line', 'figure'),
     Output('payment-pie', 'figure'),
     Output('total-sales', 'children'),
     Output('cash-sales', 'children'),
     Output('online-sales', 'children'),
     Output('highest-day', 'children'),
     Output('avg-sales', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_dashboard(start_date, end_date):
    # Filter data by the selected date range
    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    # If no data available for selected range, handle gracefully
    if filtered_df.empty:
        return go.Figure(), go.Figure(), "₹ 0", "₹ 0", "₹ 0", "N/A", "₹ 0"

    # Line chart with improvements
    line_data = filtered_df.groupby("Date")["Amount"].sum().reset_index()
    line_fig = go.Figure()

    line_fig.add_trace(go.Scatter(
        x=line_data["Date"], 
        y=line_data["Amount"],
        mode='lines+markers',
        line=dict(color='royalblue', width=3, shape='spline'),
        marker=dict(size=7, color='royalblue', symbol='circle', line=dict(color='black', width=1)),
        name='Sales'
    ))

    line_fig.update_layout(
        title="Daily Sales",
        title_x=0.5,
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0.1)',
        margin=dict(l=20, r=20, t=40, b=20),
        transition_duration=500
    )

    # Pie chart with better colors and labels
    pie_data = filtered_df.groupby("Payment Mode")["Amount"].sum().reset_index()
    pie_fig = px.pie(pie_data, values="Amount", names="Payment Mode", title="Payment Breakdown", hole=0.4)
    pie_fig.update_traces(
        textinfo='percent+label',
        pull=[0.1, 0.1],
        marker=dict(colors=['#007bff', '#28a745', '#ffc107'])
    )
    pie_fig.update_layout(
        template='plotly_dark',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Summary stats
    total = filtered_df["Amount"].sum()
    cash = filtered_df[filtered_df["Payment Mode"] == "Cash"]["Amount"].sum()
    online = filtered_df[filtered_df["Payment Mode"] == "Online"]["Amount"].sum()

    # Highest sales day of the week
    weekly_sales = filtered_df.groupby(['Week', 'Weekday'])['Amount'].sum().reset_index()
    highest_sales_day = weekly_sales.loc[weekly_sales.groupby('Week')['Amount'].idxmax()].reset_index(drop=True)
    highest_day = highest_sales_day[['Week', 'Weekday', 'Amount']]

    # Average daily sales
    avg_sales = filtered_df["Amount"].mean()

    return line_fig, pie_fig, f"₹ {total:,.0f}", f"₹ {cash:,.0f}", f"₹ {online:,.0f}", f"Week: {highest_day['Week'][0]} - {highest_day['Weekday'][0]}: ₹ {highest_day['Amount'][0]:,.0f}", f"₹ {avg_sales:,.0f}"

if __name__ == "__main__":
    app.run_server(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=False
    )
