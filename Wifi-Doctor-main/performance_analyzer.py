import pandas as pd
import numpy as np


def rate_gap(csv_file, max_mcs):
    """
    Rate_Gap = MCS_theoretical - MCS_observed

    For the AP that we are observing we find the best theoretical throughput.
    Specifically, we find how many spatial streams it can support; 
    hence the max MCS index.

    By having the max MCS aka the theoretical MCS we go through all the packets 
    (we filter only: data frame packets, destination address to be a specific device, 
    source address to be a specific AP and packets that do have a MCS index)
    and we measure the rate gap for each.

    Unlike the previous version, this function returns *all* per-packet
    rate_gap values and their wireshark_timestamp, rather than an average.

    Args:
        csv_file (str): Path to the CSV file.
        max_mcs (int): Maximum MCS index (theoretical).

    Returns:
        pd.DataFrame: DataFrame with columns:
            - 'timestamp_wireshark'
            - 'rate_gap'
    """
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Convert fc_type and mcs_index to numeric if necessary
    df['fc_type'] = pd.to_numeric(df['fc_type'], errors='coerce')
    df['mcs_index'] = pd.to_numeric(df['mcs_index'], errors='coerce')

    # Normalize MAC addresses (ta and ra) to uppercase and strip whitespace
    df['ta'] = df['ta'].str.upper().str.strip()
    df['ra'] = df['ra'].str.upper().str.strip()

    print(f"Initial DataFrame shape: {df.shape}")

    # Filter the DataFrame for packets with MCS index and the specified conditions
    filtered_df = df[
        (df['fc_type'] == 2) &
        (df['ta'] == "E0:B6:68:1B:B4:CF") &
        (df['ra'] == "2C:3B:70:58:39:5D")&
        df['mcs_index']!=0  # ensure mcs_index is present
    ].copy()

    print(f"Filtered DataFrame shape: {filtered_df.shape}")

    # Calculate the rate gap for each packet: (max_mcs - observed_mcs)
    filtered_df['rate_gap'] = max_mcs - filtered_df['mcs_index']

    # Return only timestamp and rate_gap
    if 'timestamp_wireshark' not in filtered_df.columns:
        raise ValueError("The CSV file must contain 'timestamp_wireshark' column.")

    result_df = filtered_df[['timestamp_wireshark', 'rate_gap']]

    return result_df
def filter_downlink_frames_values(csv_file):
    """
    Reads the CSV file at `csv_file`, filters it for data frames (fc_type == 2)
    where:
      - ta == 'E0:B6:68:1B:B4:CF'(transmitter)
      - ra == '2C:3B:70:58:39:5D' (receiver)

    Returns a DataFrame with just the columns:
      - timestamp_wireshark
      - signal_strength (RSSI)
      - data_rate
    """

    # Read the CSV into a DataFrame
    df = pd.read_csv(csv_file)

    # Ensure columns exist
    required_cols = ['timestamp_wireshark', 'fc_type', 'ta', 'ra', 'signal_strength', 'data_rate']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CSV must contain a '{col}' column.")

    # Convert relevant columns to numeric (in case they're strings)
    df['fc_type'] = pd.to_numeric(df['fc_type'], errors='coerce')
    df['data_rate'] = pd.to_numeric(df['data_rate'], errors='coerce')
    df['signal_strength'] = pd.to_numeric(df['signal_strength'], errors='coerce')

    # Normalize MAC addresses (ta and ra) to uppercase and strip whitespace
    df['ta'] = df['ta'].str.upper().str.strip()
    df['ra'] = df['ra'].str.upper().str.strip()

    print(f"Initial DataFrame shape: {df.shape}")

    # Filter the DataFrame for packets matching the filter criteria
    filtered_df = df[
        (df['fc_type'] == 2) &
        (df['ta'] == "E0:B6:68:1B:B4:CF") &
        (df['ra'] == "2C:3B:70:58:39:5D")
    ]
    # wanted values
    columns_of_interest = [
        'timestamp_wireshark',
        'signal_strength',
        'data_rate'
    ]
    result_df = filtered_df [columns_of_interest]

    # testing
    if not result_df.empty:
        print("Filtered results (first 5 rows):")
        print(result_df.head())
    else:
        print("No frames matched the filter criteria.")

    return result_df

if __name__ == "__main__":
    csv_file = 'mikehome1.csv'
    max_mcs = 15  # maximum MCS index found from wireshark
    average_gap = rate_gap(csv_file, max_mcs)
    print(average_gap)
  
    filtered_df = filter_downlink_frames_values("mikehome1.csv")
    print(filtered_df)