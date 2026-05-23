import pyshark
import pandas as pd
import datetime

pcap_file = '/home/pavlos/Documents/captures_home_pavlos/2.4_home_pavlos.pcapng'


# Helper function to get fields from pyshark layers
def get_field(layer, attr):
    try:
        return getattr(layer, attr)
    except Exception:
        return None
    
# Helper function to get raw fields from pyshark layers 
def get_raw_field(packet, layername, key):
    try:
        return packet[layername]._all_fields.get(key)
    except Exception:
        return None

# Store parsed data here
packet_data = []

try:
    cap = pyshark.FileCapture(pcap_file, only_summaries=False, use_json=False)

    for i, packet in enumerate(cap):
   

        # Special treatment for timestamp otherwise it doesnt recognize fixed_timestamp from layer wlan.mgt
        tsf_timestamp = None
        try:
            if 'wlan.mgt' in packet:
                tsf = packet['wlan.mgt'].get_field('wlan_fixed_timestamp')
                if tsf:
                    tsf_timestamp = tsf
        except Exception:
            pass
        
       


        # Building the packet dictionary
        pkt = {
            "packet_number": get_field(packet, 'number'),
            "length": get_field(packet, 'length'),
            "bssid": get_field(getattr(packet, 'wlan', None), 'bssid'),
            "ta": get_field(getattr(packet, 'wlan', None), 'ta'),
            "ra": get_field(getattr(packet, 'wlan', None), 'ra'),
            "fc_type_subtype": get_field(getattr(packet, 'wlan', None), 'fc_type_subtype'),
            "data_rate": get_field(getattr(packet, 'wlan_radio', None), 'data_rate'),
            "channel": get_field(getattr(packet, 'wlan_radio', None), 'channel'),
            "frequency": get_field(getattr(packet, 'wlan_radio', None), 'frequency'),
            "phy": get_field(getattr(packet, 'wlan_radio', None), 'phy'),
            "retry": get_field(getattr(packet, 'wlan', None), 'fc_retry'),
            "data_rate": get_field(getattr(packet, 'wlan_radio', None), 'data_rate'),
            "short_gi": get_field(getattr(packet, 'radiotap', None), 'flags_shortgi'),
            "signal_strength": get_field(getattr(packet, 'wlan_radio', None), 'signal_dbm'),
            "bandwidth": get_raw_field(packet, 'wlan_radio', 'wlan_radio.11ac.bandwidth'),
            "mcs_index": get_raw_field(packet, 'radiotap', 'radiotap.mcs.index'),
            "tsf_timestamp": tsf_timestamp, # in wireshark its inside wifi manager its the APs timestamp 
            "timestamp_wireshark" : float(packet.frame_info.time_epoch), # for beacon jitter and plotting
        }

        # Append the packet data
        packet_data.append(pkt)

    # Create DataFrame and save CSV
    df = pd.DataFrame(packet_data)

    # making readable time from wireshark
    df['timestamp_readable'] = df['timestamp_wireshark'].apply(
    lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S.%f')
)
    # maybe use the file in libreoffice calc or excel
    df.to_csv("2.4_home.csv", index=False)
    print("CSV saved.")

except FileNotFoundError:
    print(f"Error: The file {pcap_file} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
