#!/usr/bin/env python
"""
This module provides functionality for generating various reports.

It includes functions to:
- Generate blockchain holdings reports.
- Export reports to HTML format.
- Perform data aggregation and analysis for reporting purposes.

Functions:
- generate_blockchain_holdings_report: Generates a report of blockchain holdings and exports it to an HTML file.
- export_to_html: Exports the given data to an HTML file.
- aggregate_data: Aggregates data for reporting purposes.
- analyze_data: Analyzes data to extract meaningful insights for reports.
"""

import sqlite3
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Connect to your SQLite database
conn = sqlite3.connect('db/portfolio_history.db')
cursor = conn.cursor()

# Example query for total value over time by chain
QUERY1 = """
SELECT 
    i.run_date, 
    c.name as chain_name, 
    SUM(wt.value) as total_value
FROM 
    import_run i
    JOIN wallet_token wt ON i.id = wt.import_run_id
    JOIN chain c ON wt.chain_id = c.id
GROUP BY 
    i.run_date, c.name
ORDER BY 
    i.run_date, total_value DESC
"""

# Example query for top tokens by value
QUERY2 = """
SELECT 
    t.name as token_name,
    SUM(wt.value) as total_value
FROM 
    wallet_token wt
    JOIN token t ON wt.token_id = t.id
    JOIN import_run i ON wt.import_run_id = i.id
WHERE 
    i.run_date = (SELECT MAX(run_date) FROM import_run)
GROUP BY 
    t.name
ORDER BY 
    total_value DESC
LIMIT 10
"""

# Execute queries
cursor.execute(QUERY1)
results1 = cursor.fetchall()

cursor.execute(QUERY2)
results2 = cursor.fetchall()

# Close the connection
conn.close()

# Prepare data for plotting
dates = list({r[0] for r in results1})
chains = list({r[1] for r in results1})
values = {chain: [0]*len(dates) for chain in chains}

for r in results1:
    date_index = dates.index(r[0])
    values[r[1]][date_index] = r[2]

# Create subplots
fig = make_subplots(rows=2, cols=1, subplot_titles=("Total Value Over Time by Chain", "Top 10 Tokens by Value"))

# Add traces for each chain
for chain in chains:
    fig.add_trace(go.Scatter(x=dates, y=values[chain], name=chain, stackgroup='one'), row=1, col=1)

# Add bar chart for top tokens
fig.add_trace(go.Bar(x=[r[0] for r in results2], y=[r[1] for r in results2]), row=2, col=1)

# Update layout
fig.update_layout(height=900, width=1200, title_text="Blockchain Holdings Report")
fig.update_xaxes(title_text="Date", row=1, col=1)
fig.update_xaxes(title_text="Token", row=2, col=1)
fig.update_yaxes(title_text="Total Value", row=1, col=1)
fig.update_yaxes(title_text="Value", row=2, col=1)

# Show the plot
fig.show()

# Optionally, save to HTML file
fig.write_html("blockchain_holdings_report.html")
