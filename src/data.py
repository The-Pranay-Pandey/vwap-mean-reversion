import glob
import subprocess
import pandas as pd
from src.config import instrument, start, end, timeframe


def fetch_data():
    """Download data from Dukascopy (requires Node.js / npx)."""
    subprocess.run([
        "npx", "dukascopy-node",
        "-i", instrument,
        "-from", start,
        "-to", end,
        "-t", timeframe,
        "-f", "csv",
        "-v", "true"
    ], check=True)


def load_data():
    """Load the downloaded csv and index it by UTC timestamp."""
    file = glob.glob(f"download/{instrument}-{timeframe}*.csv")
    if not file:
        raise FileNotFoundError("No data found in download/. Run fetch_data() first.")
    data = pd.read_csv(file[0])
    # adjusting time
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit='ms', utc=True)
    data.set_index("timestamp", inplace=True)
    return data
