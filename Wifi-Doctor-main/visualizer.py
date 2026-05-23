import os

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from performance_monitor import beacon_jitter_intervals, rssi_based_overlap_index, overlap_tot_avg, compute_rssid_from_csv,jitter_tot_avg, throughput_comp
from performance_analyzer import rate_gap,filter_downlink_frames_values


def plot_beacon_jitter(jitter_df, top_n=3, output_filename="beacon_jitter_top_n.png"):
    """
    Plots beacon jitter over time for the top_n APs using the jitter_df
    provided as input. This function assumes jitter_df is the DataFrame returned by
    beacon_jitter_intervals.

    Parameters:
        jitter_df (DataFrame): A DataFrame with columns:
            - timestamp_wireshark 
            - jitter_ms (jitter in milliseconds)
            - MAC adr 
        top_n (int): Number of top APs to plot.
        output_filename (str): saved plot.
    """
    # Convert the numeric timestamp to datetime for plotting
    jitter_df['datetime'] = pd.to_datetime(jitter_df['timestamp_wireshark'], unit='s')
    
    plt.figure(figsize=(12, 6))
    
    # Pick the most frequent beacons for ploting 
    top_bssids = jitter_df['bssid'].value_counts().nlargest(top_n).index.tolist()
    filtered_df = jitter_df[jitter_df['bssid'].isin(top_bssids)]
    
    # Plot jitter over time for each of APs choosen above
    for bssid, group in filtered_df.groupby('bssid'):
        plt.plot(group['datetime'], group['jitter_ms'], linestyle='-', label=bssid)
    
    plt.xlabel("Time")
    plt.ylabel("Beacon Jitter (ms)")
    plt.title(f"Beacon Jitter Over Time for Top {top_n} APs")
    plt.legend(title="MAC address", bbox_to_anchor=(0.90, 1), loc="upper left")
    plt.grid(True)
    plt.subplots_adjust(bottom=0.15, top=0.9)
    
    plt.savefig(output_filename)
    plt.close()
    print(f"Plot saved as {output_filename}")

def plot_avg_overlap(scenario_avgs, output_filename="average_overlap_index_comparison.png"):
    """
    Plots a bar chart of the average overlap index for each scenario.
    
    Parameters:
        scenario_avgs (dict): A dictionary where the keys are scenario names (e.g., "5GHz Home")
                              and the values are the average overlap index (scalar numeric values).
        output_filename (str): Filename to save the plot.
    """
    scenarios = list(scenario_avgs.keys())
    values = [scenario_avgs[sc] for sc in scenarios]
    
    # Ensure values are scalar
    if any(isinstance(val, (list, np.ndarray)) for val in values):
        raise ValueError("All values must be scalar (not lists or arrays).")
    
    plt.figure(figsize=(10, 6))

    colors = ["blue", "green", "orange", "red"]
    plt.bar(scenarios, values, color=colors[:len(scenarios)], edgecolor="black")

    plt.xlabel("Scenario")
    plt.ylabel("Average Overlap Index")
    plt.title("Average Overlap Index per Scenario")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()
    print(f"Bar chart saved as {output_filename}")


def plot_rssids(scenarios_rssid, output_filename="rssid.png"):
    """
    Plots a bar chart of the bssid for each scenario.
    
    Parameters:
        scenario_avgs (dict): A dictionary where the keys are scenario names (e.g., "5GHz Home")
                              and the values are the average overlap index (scalar numeric values).
        output_filename (str): Filename to save the plot.
    """
    scenarios = list(scenarios_rssid.keys())
    values = [scenarios_rssid[sc] for sc in scenarios]
    
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, values, color=["magenta", "purple", "orange", "red"], edgecolor="black")
    plt.xlabel("Scenario")
    plt.ylabel("Total RSSID")
    plt.title("Total RSSID per Scenario")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()
    print(f"Bar chart saved as {output_filename}")


def plot_avg_jitter(scenario_avg_jitter, output_filename="avg_jitter.png"):
    """
    Plots a bar chart of the jitter average for each scenario.
    
    Parameters:
        scenario_avgs (dict): A dictionary where the keys are scenario names (e.g., "5GHz Home")
                              and the values are the average overlap index (scalar numeric values).
        output_filename (str): Filename to save the plot.
    """
    scenarios = list(scenario_avg_jitter.keys())
    values = [scenario_avg_jitter[sc] for sc in scenarios]
    
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, values, color=["red", "blue", "orange", "green"], edgecolor="black")
    plt.xlabel("Scenario")
    plt.ylabel("Avg jitter ms")
    plt.title("Average jitter per Scenario")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()
    print(f"Bar chart saved as {output_filename}")


def plot_data_rate_timeseries(df_rssi_datarate, output_file='data_rate_timeseries.png'):
    """
    Plots a time series of Data Rate over timestamp_wireshark, 
    then saves the figure as a PNG (no explicit colors or subplots).
    
    :param df: pandas DataFrame with columns:
        - 'timestamp_wireshark'
        - 'data_rate'
    :param output_file: filename or path for the PNG output
    """
    if 'timestamp_wireshark' not in df_rssi_datarate.columns or 'data_rate' not in df_rssi_datarate.columns:
        raise ValueError("DataFrame must have 'timestamp_wireshark' and 'data_rate' columns.")

    plt.figure()
    plt.plot(df_rssi_datarate['timestamp_wireshark'], df_rssi_datarate['data_rate'])
    plt.xlabel('Time (Wireshark Timestamp)')
    plt.ylabel('Data Rate (Mbps)')
    plt.title('Data Rate Over Time')
    plt.savefig(output_file, dpi=300)
    plt.close()


def plot_rate_gap_timeseries(df_rate_gap, output_file='rate_gap_timeseries.png'):
    """
    Plots a time series of Rate Gap over timestamp_wireshark, 
    then saves the figure as a PNG.
    
    :param df: pandas DataFrame with columns:
        - 'timestamp_wireshark'
        - 'rate_gap'
    :param output_file: filename or path for the PNG output
    """
    if 'timestamp_wireshark' not in df_rate_gap.columns or 'rate_gap' not in df_rate_gap.columns:
        raise ValueError("DataFrame must have 'timestamp_wireshark' and 'rate_gap' columns.")

    plt.figure()
    plt.plot(df_rate_gap['timestamp_wireshark'], df_rate_gap['rate_gap'])
    plt.xlabel('Time (Wireshark Timestamp)')
    plt.ylabel('Rate Gap')
    plt.title('Rate Gap Over Time')
    plt.savefig(output_file, dpi=300)
    plt.close()


def plot_rssi_timeseries(df_rssi_datarate, output_file='rssi_timeseries.png'):
    """
    Plots a time series of RSSI (signal_strength) over timestamp_wireshark,
    then saves the figure as a PNG.
    
    :param df: pandas DataFrame with columns:
        - 'timestamp_wireshark'
        - 'signal_strength'
    :param output_file: filename or path for the PNG output
    """
    if 'timestamp_wireshark' not in df_rssi_datarate.columns or 'signal_strength' not in df_rssi_datarate.columns:
        raise ValueError("DataFrame must have 'timestamp_wireshark' and 'signal_strength' columns.")

    plt.figure()
    plt.plot(df_rssi_datarate['timestamp_wireshark'], df_rssi_datarate['signal_strength'])
    plt.xlabel('Time (Wireshark Timestamp)')
    plt.ylabel('Signal Strength (dBm)')
    plt.title('RSSI Over Time')
    plt.savefig(output_file, dpi=300)
    plt.close()



def plot_frame_losses_timeseries(csv_file, output_file='frame_losses_timeseries.png'):
    """
    Plots a time series of frame losses over time intervals using the throughput_comp function,
    then saves the figure as a PNG.

    :param csv_file: Path to the CSV file containing packet data.
    :param output_file: Filename or path for the PNG output.
    """
    # Use throughput_comp to get the filtered DataFrame, frame loss rate, and frame losses over time
    _, _, frame_losses_over_time = throughput_comp(csv_file)

    # Check if the DataFrame is empty
    if frame_losses_over_time.empty:
        print("The frame_losses_over_time DataFrame is empty. No plot will be generated.")
        return

    # Plot frame losses over time
    plt.figure(figsize=(12, 6))
    plt.plot(frame_losses_over_time['time_bin'], frame_losses_over_time['frame_losses'], 
             label='Frame Losses', color='red')
    plt.xlabel('Time (Seconds)')
    plt.ylabel('Frame Losses')
    plt.title('Frame Losses Over Time')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"Frame losses time series plot saved as {output_file}")


def align_frame_losses_with_data_rate(csv_file, output_file='aligned_comparison_plot.png'):
    """
    Aligns frame losses with data rate timestamps and plots them together for comparison.

    :param csv_file: Path to the CSV file containing packet data.
    :param output_file: Filename or path for the PNG output.
    """
    # Use throughput_comp to get the filtered DataFrame
    result_df, _, _ = throughput_comp(csv_file)

    # Check if the DataFrame is empty
    if result_df.empty:
        print("The result DataFrame is empty. No plot will be generated.")
        return

    # Align frame losses with data rate timestamps
    aligned_frame_losses = result_df.groupby('timestamp_wireshark')['frame_loss'].sum()

    # Plot data rate and aligned frame losses
    plt.figure(figsize=(12, 6))

    # Plot data rate
    plt.plot(result_df['timestamp_wireshark'], result_df['data_rate'], label='Data Rate (Mbps)', color='blue')

    # Plot aligned frame losses (scaled for visualization)
    plt.plot(aligned_frame_losses.index, aligned_frame_losses * max(result_df['data_rate']), 
             label='Frame Losses (Scaled)', color='red', alpha=0.7)

    # Add labels and legend
    plt.xlabel('Time (Wireshark Timestamp)')
    plt.ylabel('Data Rate (Mbps)')
    plt.title('Comparison of Data Rate and Frame Losses Over Time')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"Aligned comparison plot saved as {output_file}")


def plot_throughput_with_frame_loss(csv_file, output_file='throughput_with_frame_loss.png'):
    """
    Calculates and plots throughput based on data rate and frame losses over time.

    Throughput is calculated as:
        throughput = data_rate * (1 - aligned_frame_losses)

    :param csv_file: Path to the CSV file containing packet data.
    :param output_file: Filename or path for the PNG output.
    """
    # Use throughput_comp to get the filtered DataFrame
    result_df, _, _ = throughput_comp(csv_file)

    # Check if the DataFrame is empty
    if result_df.empty:
        print("The result DataFrame is empty. No plot will be generated.")
        return

    # Align frame losses with data rate timestamps
    aligned_frame_losses = result_df.groupby('timestamp_wireshark')['frame_loss'].sum()

    # Calculate throughput: throughput = data_rate * (1 - aligned_frame_losses)
    throughput_plot = result_df.copy()
    throughput_plot['aligned_frame_loss'] = throughput_plot['timestamp_wireshark'].map(aligned_frame_losses)
    throughput_plot['aligned_frame_loss'] = throughput_plot['aligned_frame_loss'].fillna(0)  # Fill missing losses with 0
    throughput_plot['throughput'] = throughput_plot['data_rate'] * (1 - throughput_plot['aligned_frame_loss'])

    # Plot throughput over time
    plt.figure(figsize=(12, 6))
    plt.plot(throughput_plot['timestamp_wireshark'], throughput_plot['throughput'], label='Throughput (Mbps)', color='green')

    # Add labels and legend
    plt.xlabel('Time (Wireshark Timestamp)')
    plt.ylabel('Throughput (Mbps)')
    plt.title('Throughput Over Time (Considering Frame Losses)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"Throughput plot saved as {output_file}")


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":

    # CSV files 
    input_csv_single_channel_5home_1ch = '5_home_one.csv'
    input_csv_single_channel_5mall_1ch = '5_riverwest_one.csv'
    input_csv_single_channel_24home_1ch = '2.4_home_one.csv'
    input_csv_single_channel_24mall_1ch = '2.4_riverwest_one.csv'
    
    input_csv_channel_5home  = '5_home.csv'
    input_csv_channel_5mall  = '5_riverwest.csv'
    input_csv_channel_24home = '2.4_home.csv'
    input_csv_channel_24mall = '2.4_riverwest.csv'

    # Compute jitter
    beacon_jitter_df_5h  = beacon_jitter_intervals(input_csv_single_channel_5home_1ch)
    beacon_jitter_df_5m  = beacon_jitter_intervals(input_csv_single_channel_5mall_1ch)
    beacon_jitter_df_24h = beacon_jitter_intervals(input_csv_single_channel_24home_1ch)
    beacon_jitter_df_24m = beacon_jitter_intervals(input_csv_single_channel_24mall_1ch)

    # avg jitter
    summary_5h  = jitter_tot_avg(beacon_jitter_df_5h)
    mean_jitter_ms_5h = summary_5h['avg_jitter_ms'].iloc[0] #extracting the mean in ms
    summary_5m  = jitter_tot_avg( beacon_jitter_df_5m)
    mean_jitter_ms_5m = summary_5m['avg_jitter_ms'].iloc[0] 
    summary_24h = jitter_tot_avg(beacon_jitter_df_24h)
    mean_jitter_ms_24h = summary_24h['avg_jitter_ms'].iloc[0] 
    summary_24m = jitter_tot_avg(beacon_jitter_df_24m)
    mean_jitter_ms_24m = summary_24m['avg_jitter_ms'].iloc[0] 

    # Average overlapping channels
    overlap_df_5h,chsummary5h  = rssi_based_overlap_index(input_csv_channel_5home,-75)
    overlap_df_5m,chsummary5m  = rssi_based_overlap_index(input_csv_channel_5mall,-75)
    overlap_df_24h,chsummary24h = rssi_based_overlap_index(input_csv_channel_24home,-75)
    overlap_df_24m,chsummary24m  = rssi_based_overlap_index(input_csv_channel_24mall,-75)

    avg_ch_5h  = overlap_tot_avg( chsummary5h)
    avg_ch_5m  = overlap_tot_avg( chsummary5m) 
    avg_ch_24h = overlap_tot_avg( chsummary24h)
    avg_ch_24m = overlap_tot_avg( chsummary24m)

    # RSSID
    rssid_5home_val,rssid_5home_total = compute_rssid_from_csv(input_csv_channel_5home)
    rssid_5mall_val,rssid_5mall_total = compute_rssid_from_csv(input_csv_channel_5mall)
    rssid_24h_val,  rssid_24home_total   = compute_rssid_from_csv(input_csv_channel_24home)
    rssid24m_val,  rssid24mall_total  = compute_rssid_from_csv( input_csv_channel_24mall)

    # Input for ploting avg channel overal
    scenario_avgs = {
    "5GHz Home": avg_ch_5h,
    "5GHz Mall": avg_ch_5m,
    "2.4GHz Home": avg_ch_24h,
    "2.4GHz Mall": avg_ch_24m
    }
    
    # Input for ploting rssid
    scenarios_rssid = {
    "5GHz Home": rssid_5home_total,
    "5GHz Mall": rssid_5mall_total,
    "2.4GHz Home": rssid_24home_total,
    "2.4GHz Mall": rssid24mall_total
    }

    # Input for ploting avg jitter
    scenario_avg_jitter={
    "5GHz Home": mean_jitter_ms_5h,
    "5GHz Mall": mean_jitter_ms_5m,
    "2.4GHz Home": mean_jitter_ms_24h,
    "2.4GHz Mall": mean_jitter_ms_24m
    }

    df_rssi_datarate = filter_downlink_frames_values('mikehome1.csv')
    df_rate_gap = rate_gap('mikehome1.csv',15)

    # plots for each scenario-----------------------------------------------------------------------------------------------------
    

    

    # Call the function to clear the termindef clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    clear_terminal()

    # jitter
    plot_beacon_jitter(beacon_jitter_df_5h, top_n=2, output_filename="beacon_jitter_5_home.png")
    plot_beacon_jitter(beacon_jitter_df_5m, top_n=2, output_filename="beacon_jitter_5_mall.png")
    plot_beacon_jitter(beacon_jitter_df_24h, top_n=3, output_filename="beacon_jitter_2.4_home.png")
    plot_beacon_jitter(beacon_jitter_df_24m, top_n=2, output_filename="beacon_jitter_2.4_mall.png")
    
    # channel overlap
    plot_avg_overlap(scenario_avgs)
   
    # rssid
    plot_rssids(scenarios_rssid)

    # avg jitter
    plot_avg_jitter(scenario_avg_jitter)
    
    # 1) Plot data rate over time, save to "data_rate.png"
    plot_data_rate_timeseries(df_rssi_datarate, output_file='data_rate.png')

    # 2) Plot rate gap over time, save to "rate_gap.png"
    plot_rate_gap_timeseries(df_rate_gap, output_file='rate_gap.png')

    # 3) Plot RSSI over time, save to "rssi.png"
    plot_rssi_timeseries(df_rssi_datarate, output_file='rssi_mike.png')


    # 4) Plot frame loss time series
    csv_file = 'mikehome1.csv'
    # Additional plot for frame losses timeseries
    plot_frame_losses_timeseries(csv_file , output_file='frame_losses_timeseries.png')

    # 5) Align frame losses with data rate and plot comparison
    align_frame_losses_with_data_rate(csv_file, output_file='aligned_comparison_plot.png')

    # 6) Plot throughput considering frame loss
    plot_throughput_with_frame_loss(csv_file, output_file='throughput_with_frame_loss.png')