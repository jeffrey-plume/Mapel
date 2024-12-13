import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go
import sqlite3
import plotly.io as pio  # Import pio properly

class FitService:
    def __init__(self, conn, web_view=None):
        """Initialize with the path to the SQLite database."""
        self.conn = conn
        self.web_view = web_view  # Store the web_view instance for rendering HTML

    def fetch_data_from_sql(self, query):
        """Fetch data from the SQLite database and return a DataFrame."""
        try:
            df = pd.read_sql_query(query, self.conn)
            print(df)
            return df
        except Exception as e:
            print(f"Error fetching data from database: {e}")
            return pd.DataFrame()

    @staticmethod
    def four_parameter_logistic(x, A, B, C, D):
        """Four-parameter logistic (4PL) model function."""
        return D + (A - D) / (1 + (x / C) ** B)

    def fit_and_plot(self, df):
        """Fit the 4PL model and visualize the result using Plotly."""
        # Assuming the columns are 'Conc' for dose and 'POC' for response
        x_data = df['Conc'].dropna().values
        y_data = df['POC'].dropna().values

        # Apply curve fitting with initial guesses for A, B, C, D
        initial_guess = [min(y_data), 1.0, np.median(x_data), max(y_data)]
        popt, _ = curve_fit(self.four_parameter_logistic, x_data, y_data, p0=initial_guess)

        # Print the fitted parameters
        print(f"Fitted Parameters (A, B, C, D): {popt}")

        # Create the fitted curve data
        x_fit = np.linspace(min(x_data), max(x_data), 100)
        y_fit = self.four_parameter_logistic(x_fit, *popt)

        # Create the Plotly figure
        fig = go.Figure()

        # Add scatter plot of the original data
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            name='Data',
            marker=dict(color='blue')
        ))

        # Add the fitted 4PL curve
        fig.add_trace(go.Scatter(
            x=x_fit,
            y=y_fit,
            mode='lines',
            name='4PL Fit',
            line=dict(color='red')
        ))

        # Set the title and labels
        fig.update_layout(
            title="Dose Response Curve (4PL Fit)",
            xaxis_title="Dose (Conc)",
            yaxis_title="Response (POC)",
            legend_title="Legend"
        )

        return fig

    def load_and_plot(self, query):
        """Load data from SQL, fit the model, and render the plot in QWebEngineView."""
        try:
            df = self.fetch_data_from_sql(query)

            if df.empty:
                print("No data found.")
                return

            fig = self.fit_and_plot(df)

            if fig is None:
                print("Failed to generate the plot.")
                return

            html = pio.to_html(fig, full_html=False)

            if self.web_view:  # Ensure web_view is available
                self.web_view.setHtml(html)
            else:
                print("No QWebEngineView available for rendering the plot.")

        except Exception as e:
            print(f"Error loading or processing data: {e}")

