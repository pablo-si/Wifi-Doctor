import pandas as pd
from math import log
import numpy as np

"""


Density Metrics:
1)Beacon Jitter
2)Overlapping Channels given a strong RSSI(capable of interference)
3)RSSID source paper [3] 
4)PHY type percentage (old phy types may create congestion)
---------------------------------------------------------------------------
5) phy_score : creating a score for the phy type
6)overlap_tot_avg : computing average overlap to use in score and plotting
7)throughput_comp : computing throughput and frame loss rate
8)main : computing density score from all the above metrics
---------------------------------------------------------------------------



"""

def beacon_jitter_intervals(csv_file, nominal_interval=0.100):
    """
    Reads the CSV file, filters for beacon frames, and computes beacon intervals and jitter values.
    
    The CSV file should be from a capture of one channel NO CHANNEL HOPPING!!!

    Parameters:
        csv_file (str): Path to the CSV file.
        nominal_interval (float): The expected beacon interval in seconds (default is 0.100 seconds).
    
    Returns:
        DataFrame: A new DataFrame with one row per beacon interval containing:
            - bssid: The AP identifier.
            - timestamp_wireshark: Timestamp (numeric) of the beacon.
            - interval_s: The time difference (in seconds) between the current beacon and the previous beacon.
            - interval_ms: The same interval in milliseconds.
            - jitter_s: The difference between the measured interval and the nominal interval (in seconds).
            - jitter_ms: The jitter in milliseconds.
    """
    # Load the CSV file from the parser
    df = pd.read_csv(csv_file)
    
    # Filter only beacon frames 
    df_beacons = df[df['fc_type_subtype'] == "0x0008"].copy()
    
    # Sort by BSSID and then numeric timestamp 
    df_beacons.sort_values(by=['bssid', 'timestamp_wireshark'], inplace=True)
    
    # List to hold DataFrames for each BSSID
    results = []
    
    # Group by BSSID and compute raw intervals and jitter for each group
    for bssid, group in df_beacons.groupby('bssid'):

        group = group.copy()

        # Use the numeric timestamp for diff calculation
        group['interval_s'] = group['timestamp_wireshark'].diff()

        # Drop the first row for which diff() gives NaN
        group = group.dropna(subset=['interval_s'])
        
        # Convert interval to milliseconds
        group['interval_ms'] = group['interval_s'] * 1000
        
        # difference between measured interval and the nominal interval
        group['jitter_s'] = group['interval_s'] - nominal_interval
        group['jitter_ms'] = group['jitter_s'] * 1000
        
        # for later plotting
        results.append(group[['bssid', 'timestamp_wireshark', 'interval_s', 'interval_ms', 'jitter_s', 'jitter_ms']])
    
    # Concatenate results for all BSSIDs into one DataFrame
    result_df = pd.concat(results)
    
    # Print the resulting DataFrame
    print("Beacon interval and jitter values:")
    print(result_df)
    
    return result_df

def rssi_based_overlap_index(csv_file, rssi_threshold=-75):
    """
    With Channel Hopping capture.
    Computes the average overlap index per channel and band.

    Groups the overlap counts from each AP by channel and band, then calculates the
    mean number of overlapping APs per group. This provides a summary of channel
    congestion levels in both 2.4GHz and 5GHz bands.

    Returns:
        DataFrame: A table with one row per (band, channel) pair containing:
            - band (str): '2.4GHz' or '5GHz'.
            - channel (int): The Wi-Fi channel number.
            - avg_overlap_index (float): The average number of overlapping APs for
              all APs operating on that channel in that band.
    """

    df = pd.read_csv(csv_file)

    # Filter for beacon frames and get fields from csv file
    df_beacons = df[df['fc_type_subtype'] == "0x0008"].copy()
    # Remove any rows that don't have a BSSID, channel, or signal strength
    df_beacons = df_beacons.dropna(subset=['bssid', 'channel', 'signal_strength'])
    df_beacons['channel'] = pd.to_numeric(df_beacons['channel'], errors='coerce')
    df_beacons['signal_strength'] = pd.to_numeric(df_beacons['signal_strength'], errors='coerce')

    # Compute average RSSI per AP
    # Group beacons per AP (BSSID + channel) and compute average RSSI (each AP--> avg_RSSI),
    # then we filter out weak APs below the RSSI threshold to focus only on those likely to cause interference
    avg_rssi_df = df_beacons.groupby(['bssid', 'channel'])['signal_strength'].mean().reset_index()
    avg_rssi_df = avg_rssi_df[avg_rssi_df['signal_strength'] > rssi_threshold]
    
    # Mainly for the 5GHz home capture because beacons are fewer and weaker   so,
    # it's unlikely to cause interference
    if avg_rssi_df.empty:
     print(" No APs with RSSI above threshold were found")
     pass

    # Determine band (helper function-)-----------------------------------------------------------
    def get_band(ch):
        if 1 <= ch <= 14:
            return '2.4GHz'
        elif 32 <= ch <= 177:
            return '5GHz'
        else:
            return 'unknown'
    #---------------------------------------------------------------------------------------------


    avg_rssi_df['band'] = avg_rssi_df['channel'].apply(get_band)

    
    # overlap logic (helper function)-------------------------------------------------------------
    def get_overlapping_channels(ch, band):
        if band == '2.4GHz':
            if 1 <= ch <= 5:
                return list(range(1, 6)) # overlaps with 1–5
            elif 6 <= ch <= 9:
                return list(range(4, 11))# overlaps with 4–10
            elif 10 <= ch <= 14:
                return list(range(9, 15))# overlaps with 9–14
            else:
                return [ch]
        # No overlap in 5GHz, only same-channel counts 
        # because in 5GHz Wi-Fi channels are non-overlapping assuming there is no channel bonding  
        elif band == '5GHz':
            return [ch]  
        else:
            return []
    #----------------------------------------------------------------------------------------------

    overlap_data = []

    for idx, row in avg_rssi_df.iterrows():
        bssid = row['bssid']
        ch = int(row['channel'])
        rssi = row['signal_strength']
        band = row['band']
        
        # get the list of overlapping channels (using helper function)
        overlapping_channels = get_overlapping_channels(ch, band)

        overlapping_aps = avg_rssi_df[
            (avg_rssi_df['bssid'] != bssid) & # don't compare AP to it's self
            (avg_rssi_df['band'] == band) & # check only the AP's band (2.4 or 5)
            (avg_rssi_df['channel'].isin(overlapping_channels)) # only include APs on channels that overlap with the current AP’s channel
        ]

        overlap_data.append({
            'bssid': bssid,
            'channel': ch,
            'band': band,
            'avg_rssi': rssi,
            'overlapping_ap_count': len(overlapping_aps)
        })

    overlap_df = pd.DataFrame(overlap_data)

    print("RSSI-based Channel Overlap Index (per AP):")
    print(overlap_df)

    summary = overlap_df.groupby(['band', 'channel'])['overlapping_ap_count'].mean().reset_index()
    summary.columns = ['band', 'channel', 'avg_overlap_index']

    print("\n")
    print("Average Overlap Index per Channel (by band):")
    print(summary)

    return overlap_df, summary

def compute_rssid_from_csv(csv_file):
    """
    Computes RSSID (Received Signal Strength Inverse Density) for each BSSID
    based on beacon frame RSSI values.
    
    With Channel Hopping capture.

    RSSID is defined as: RSSID = sum(1 / |RSSI|) for all beacon frames from an AP.

    Parameters:
        csv_file (str): Path to the Wi-Fi CSV file (parsed from pcap).

    Returns:
        Series: A pandas Series with BSSID as index and RSSID as value.
        float: Total RSSID (sum of all APs).
    """

    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Filter for beacon frames (Wi-Fi Management subtype 0x0008)
    df_beacons = df[df['fc_type_subtype'] == "0x0008"].copy()

    # Convert signal strength to numeric
    df_beacons['signal_strength'] = pd.to_numeric(df_beacons['signal_strength'], errors='coerce')
    df_beacons = df_beacons.dropna(subset=['signal_strength'])

    # Group by BSSID and compute RSSID: sum(1 / |RSSI|)
    rssid_values = df_beacons.groupby('bssid')['signal_strength'].apply(
        lambda rssi_series: sum(1 / abs(rssi) for rssi in rssi_series if rssi != 0)
    )

    # Print results
    print("RSSID per BSSID:")
    for bssid, rssid in rssid_values.items():
        print(f"{bssid}: {rssid:.4f}")

    # Total RSSID across all APs
    total_rssid = rssid_values.sum()
    print(f"\nTotal RSSID (all APs): {total_rssid:.4f}")

    return rssid_values, total_rssid

def phy_percentage(csv_file):
    """
    Computes the distribution of PHY types (802.11 standards) based on 
    unique APs (BSSIDs) seen in the capture.

    With Channel Hopping capture.

    Each AP is counted once, using its beacon frame's advertised PHY type.

    Parameters:
        csv_file (str): Path to the parsed Wi-Fi CSV file.

    Returns:
        DataFrame: A summary with:
            - phy (str): The PHY standard (e.g., 802.11n).
            - ap_count (int): Number of unique BSSIDs using this PHY.
            - percentage (float): Percentage of total APs using this PHY.
    """

    # Load CSV
    df = pd.read_csv(csv_file)

    # Filter for beacon frames and drop missing PHY or BSSID
    df_beacons = df[df['fc_type_subtype'] == "0x0008"].dropna(subset=['bssid', 'phy'])

    # Keep only the first beacon per BSSID (to avoid counting same AP multiple times)
    first_beacons = df_beacons.drop_duplicates(subset='bssid', keep='first')

    # Count PHY types per unique AP
    phy_counts = first_beacons['phy'].value_counts().reset_index()
    phy_counts.columns = ['phy', 'ap_count']

    # Add percentages
    total_aps = phy_counts['ap_count'].sum()
    phy_counts['percentage'] = (phy_counts['ap_count'] / total_aps * 100)

    print("PHY Type Distribution (per AP):")
    print(phy_counts)
    print("\n")

    return phy_counts

def phy_score(phy_df):
    """
    Computes the PHY score based on the distribution of PHY types.

    Parameters:
        phy_df (DataFrame): DataFrame containing PHY type distribution.

    Returns:
        float: The PHY score.
    """

    def log_normalize(data_rate):
        """
        Normalizes the data rate using a logarithmic scale.
        """
        return 1 - (np.log2(data_rate) - np.log2(11)) / (np.log2(10000) - np.log2(11))

    # Define the PHY types and their corresponding data rates
    phy_types = {
        4: 11,
        5: 54,
        6: 54,
        7: 300,
        8: 7000,
        9: 10000,
    }

    # Initialize the PHY score
    phy_score = 0

    # Iterate through each row in the DataFrame
    for _, row in phy_df.iterrows():
        phy_type = row['phy']
        ap_count = row['ap_count']

        # Get the data rate for the PHY type
        data_rate = phy_types.get(phy_type, 0)

        # Skip if PHY type is not recognized
        if data_rate == 0:
            continue

        # Compute weight (1 for phy type 4, otherwise apply log_normalize)
        weight =  log_normalize(data_rate)

        # Add the weighted AP count to the total score
        phy_score += ap_count * weight

    print("PHY Score:")
    print(phy_score)
    
    return phy_score

def jitter_tot_avg(result_df):
    """
    Computes the average jitter value for all BSSIDs provided the DataFrame.

    Parameters:
        csv_file (str): Path to the CSV file.
        result_df (DataFrame): DataFrame containing jitter values for each BSSID.

    Returns:
        DataFrame: A summary with:
            - avg_jitter_s (float): The average jitter in seconds.
            - avg_jitter_ms (float): The average jitter in milliseconds.
    """
    # Ensure the DataFrame contains the necessary columns
    if 'jitter_s' not in result_df.columns or 'jitter_ms' not in result_df.columns:
        raise ValueError("The result DataFrame must contain 'jitter_s' and 'jitter_ms' columns.")

    # Compute the average jitter in seconds and milliseconds
    avg_jitter_s = result_df['jitter_s'].mean()
    avg_jitter_ms = result_df['jitter_ms'].mean()
    med_avg_jitter_s = result_df['jitter_s'].median()
    med_avg_jitter_ms = result_df['jitter_ms'].median()

    # Create a summary DataFrame
    summary_df = pd.DataFrame({
        'avg_jitter_s': [avg_jitter_s],
        'avg_jitter_ms': [avg_jitter_ms],
        'med_avg_jitter_s': [med_avg_jitter_s],
        'med_avg_jitter_ms': [med_avg_jitter_ms]
    })

    print("Average Jitter Summary:")
    print(summary_df)

    return summary_df

def overlap_tot_avg(result_df):
    """
    Computes the average overlap index for all channels and bands.

    Parameters:
        result_df (DataFrame): DataFrame containing overlap index values for each channel and band.

    Returns:
        DataFrame: A summary with:
            - avg_overlap_index (float): The average overlap index.
    """
    

    # Compute the average overlap index
    avg_overlap_index = result_df['avg_overlap_index'].mean()
    print(f"\nAverage Overlap Index:",avg_overlap_index)
    
    return avg_overlap_index

def throughput_comp (csv_file, time_interval=1):
    """
    Reads a CSV file containing packet data and computes:
      1) Overall frame loss rate (retry ratio).
      2) Throughput for each packet. [throughput = data_rate * (1 - frame_loss_rate)]
      3) Frame losses over time (grouped by time intervals).

    Parameters:
        csv_file (str): Path to the CSV file.
        time_interval (int): Time interval (in seconds) for grouping frame losses.

    Returns:
        (DataFrame, float, DataFrame): A tuple of:
            - Filtered DataFrame with added 'throughput' and 'frame_loss' columns.
            - The computed overall frame_loss_rate.
            - A DataFrame with frame losses over time.
    
    """

    # Load the CSV file
    df = pd.read_csv(csv_file)
    
    # Check for required columns
    required_cols = [
        'data_rate', 'timestamp_wireshark',
        'fc_type', 'ta', 'ra', 'retry'
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CSV file must contain a '{col}' column.")
    
    # Convert fc_type to numeric if necessary
    df['fc_type'] = pd.to_numeric(df['fc_type'], errors='coerce')

    # Normalize MAC addresses (ta and ra) to uppercase and strip whitespace
    df['ta'] = df['ta'].str.upper().str.strip()
    df['ra'] = df['ra'].str.upper().str.strip()
    
    # Filter: data frames of interest
    df_filtered = df[
        (df['fc_type'] == 2) &
        (df['ta'] == "E0:B6:68:1B:B4:CF") &
        (df['ra'] == "2C:3B:70:58:39:5D")
    ]

    # Filter further for retried frames
    df_filtered_retry = df_filtered[df_filtered['retry'] == 1]

    # Compute frame_loss_rate
    total_data_frames = len(df_filtered)
    retried_data_frames = len(df_filtered_retry)
    if total_data_frames > 0:
        frame_loss_rate = retried_data_frames / total_data_frames
    else:
        frame_loss_rate = 0.0

    print(f"Total data frames: {total_data_frames}")
    print(f"Retried data frames: {retried_data_frames}")
    print(f"Frame loss rate: {frame_loss_rate:.2%}")

    # Convert data_rate and timestamp_wireshark to numeric
    df_filtered.loc[:, 'data_rate'] = pd.to_numeric(
        df_filtered['data_rate'], errors='coerce'
    )
    df_filtered.loc[:, 'timestamp_wireshark'] = pd.to_numeric(
        df_filtered['timestamp_wireshark'], errors='coerce'
    )
    df_filtered = df_filtered.dropna(subset=['data_rate', 'timestamp_wireshark'])
    
    # Compute throughput per packet (in Mbps)
    df_filtered.loc[:, 'throughput'] = df_filtered['data_rate'] * (1 - frame_loss_rate)

    # Add a column for frame losses (binary: 1 for retried frames, 0 otherwise)
    df_filtered.loc[:, 'frame_loss'] = df_filtered['retry']

    # Calculate frame losses over time
    df_filtered['time_bin'] = (df_filtered['timestamp_wireshark'] // time_interval).astype(int)
    frame_losses_over_time = df_filtered.groupby('time_bin')['frame_loss'].sum().reset_index()
    frame_losses_over_time.columns = ['time_bin', 'frame_losses']

    return df_filtered, frame_loss_rate, frame_losses_over_time

    

if __name__ == "__main__":
    # Calling the functions created above
    input_csv = '5_home.csv'
    input_csv_single_channel = '5_home_one.csv'

    print("\n== Beacon Jitter ==\n")
    beacon_jitter_df = beacon_jitter_intervals(input_csv_single_channel)
    jitter_tot_avg(beacon_jitter_df)
    

    print("\n== RSSI-Based Overlap Index ==\n")
    overlap_df, channel_summary = rssi_based_overlap_index(input_csv)
    overlap_tot_avg(channel_summary)

    print("\n== RSSID ==\n")
    rssid_by_ap, total_rssid = compute_rssid_from_csv(input_csv)

    print("\n== PHY Summary ==\n")
    phy_summary = phy_percentage(input_csv)
    phy_score(phy_summary)

    ## Density Score 
    """
    We will call for each of our pcap files the functions created above and
    compute the density score as follows:
    Density Score = (Jitter Score + Overlap Index + RSSID + PHY Score) / 4
    where each score is normalized to a scale of 0 to 1.
    To normalize the scores, we can use min-max normalization:
    normalized_score = (score - min_score) / (max_score - min_score)
    where min_score and max_score are the minimum and maximum scores for that metric
    across all captures.
    The final density score will be a weighted average of the normalized scores:
    Density Score = w1 * normalized_jitter + w2 * normalized_overlap + w3 * normalized_rssid + w4 * normalized_phy
    where w1, w2, w3, and w4 are the weights for each metric.
    The weights can be adjusted based on the importance of each metric in the overall density score.
    In our case we will use equal weights for all metrics.
    w1 = w2 = w3 = w4 = 0.25
    """ 

    # Initialize the arrays were we will store the scores
    # for each of the metrics
    bj = np.zeros(4)    # beacon jitter
    ov = np.zeros(4)    # overlapping channels
    rssid = np.zeros(4) # RSSID
    phy = np.zeros(4)   # PHY score

    files = ['2.4_home.csv', '2.4_riverwest.csv', '5_home.csv', '5_riverwest.csv']
    files_one = ['2.4_home_one.csv', '2.4_riverwest_one.csv', '5_home_one.csv', '5_riverwest_one.csv']

    for i, file in enumerate(files):
        
        metric = file.replace('.csv', '')
        print("\n===========================================================================================")
        print("\nMetrics for :", metric)
        print("\n")
        overlap_df, channel_summary = rssi_based_overlap_index(file)
        ov[i] = overlap_tot_avg(channel_summary)
        print("\n")
        rssid_by_ap, total_rssid = compute_rssid_from_csv(file)
        rssid[i] = total_rssid
        print("\n")
        phy_summary = phy_percentage(file)
        phy[i] = phy_score(phy_summary)
        print("\n")

    for i, file in enumerate(files_one):
        # Compute beacon jitter
        metric = file.replace('.csv', '')
        print("\n===========================================================================================")
        print("\nMetrics for :", metric)
        print("\n")
        beacon_jitter_df = beacon_jitter_intervals(file)
        bj[i] = jitter_tot_avg(beacon_jitter_df)['avg_jitter_ms'][0]

    for bj_, ov_, rssid_, phy_ in zip(bj, ov, rssid, phy):
        # Normalize the scores
        normalized_bj = (bj - min(bj)) / (max(bj) - min(bj))
        normalized_ov = (ov - min(ov)) / (max(ov) - min(ov))
        normalized_rssid = (rssid - min(rssid)) / (max(rssid) - min(rssid))
        normalized_phy = (phy - min(phy)) / (max(phy) - min(phy))

    # Compute the density score
    bj_weight = 0.25
    ov_weight = 0.25
    rssid_weight = 0.25
    phy_weight = 0.25

    density_score = bj_weight * normalized_bj + ov_weight * normalized_ov + rssid_weight* normalized_rssid + phy_weight * normalized_phy
    
    # Set in 1 to 10 scale
    density_score = (density_score * 9) + 1
    print(f"\n=============== Density Scores (1 - 10) ===============\n")
    print(f"Density score for 2.4_home : {np.round(density_score[0],4)}")
    print(f"Density score for 2.4_enterprise : {np.round(density_score[1],4)}")
    print(f"Density score for 5_home : {np.round(density_score[2],4)}")
    print(f"Density score for 5_enterprise : {np.round(density_score[3],4)}\n")
    print(f"\n====================== Frame Loss Rate ========================\n")

    csv_file = 'mikehome1.csv'
    
    # Capture both the filtered DataFrame and the computed frame_loss_rate
    result_df, computed_loss_rate, frame_losses_over_time = throughput_comp(csv_file)
    
    if not result_df.empty:
        print("\n======= Throughput per Packet =======\n")
        print(result_df[['data_rate', 'throughput']])
        
        # Print the average throughput
        avg_throughput = result_df['throughput'].mean()
        print("\n======= Average Throughput =======\n")
        print(f"Average Throughput: {avg_throughput:.2f} Mbps\n")
        
    else:
        print("No matching packets found with the specified filters.")





    
