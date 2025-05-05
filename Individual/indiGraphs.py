import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

# Set the style for better-looking graphs
plt.style.use('ggplot')
sns.set_palette("colorblind")

def analyze_iperf_data(file_path):
    # Load the JSON data
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract test info
    try:
        test_start = data['start']
        intervals = data['intervals']
        
        # Extract connection info
        protocol = test_start['test_start']['protocol']
        host = test_start['connecting_to']['host']
        version = test_start['version']
        
        # Extract time series data from intervals
        time_data = []
        for interval in intervals:
            for stream in interval['streams']:
                entry = {
                    'start': interval['sum']['start'],
                    'end': interval['sum']['end'],
                    'seconds': stream['end'] - stream['start'],
                    'bytes': stream['bytes'],
                    'bits_per_second': stream['bits_per_second'],
                    'retransmits': stream.get('retransmits', 0),
                    'snd_cwnd': stream.get('snd_cwnd', 0),
                    'rtt': stream.get('rtt', 0),
                    'omitted': interval['sum'].get('omitted', False)
                }
                time_data.append(entry)
        
        # Create DataFrame for easier analysis
        df = pd.DataFrame(time_data)
        
        # Add calculated time point for x-axis
        if not df.empty:
            df['time_point'] = df['start']
            df['time_point'] = df['time_point'] - df['time_point'].min()
            
            # Create a summary section
            summary = {
                'protocol': protocol,
                'host': host,
                'version': version,
                'avg_bandwidth_mbps': df['bits_per_second'].mean() / 1_000_000,
                'max_bandwidth_mbps': df['bits_per_second'].max() / 1_000_000,
                'min_bandwidth_mbps': df['bits_per_second'].min() / 1_000_000,
                'std_bandwidth_mbps': df['bits_per_second'].std() / 1_000_000,
                'duration_seconds': df['time_point'].max(),
                'total_bytes': df['bytes'].sum()
            }
            
            if 'rtt' in df and df['rtt'].sum() > 0:
                summary['avg_rtt_ms'] = df['rtt'].mean() / 1000  # Convert to ms
            
            if 'retransmits' in df:
                summary['total_retransmits'] = df['retransmits'].sum()
            
            return df, summary
        else:
            print("No interval data found in the file.")
            return None, None
    except KeyError as e:
        print(f"Error parsing JSON: {e}")
        return None, None

def create_visualizations(df, summary, algorithm):
    if df is None:
        return
    
    # Create a figure with multiple subplots
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Throughput over time
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(df['time_point'], df['bits_per_second'] / 1_000_000, 'b-', linewidth=2)
    ax1.set_title(f'Throughput Over Time ({algorithm})', fontsize=14)
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('Throughput (Mbps)', fontsize=12)
    ax1.grid(True)
    
    # Add a horizontal line for average throughput
    ax1.axhline(y=summary['avg_bandwidth_mbps'], color='r', linestyle='--', 
               label=f'Avg: {summary["avg_bandwidth_mbps"]:.2f} Mbps')
    ax1.legend()
    
    # 2. Bandwidth distribution (histogram)
    ax2 = plt.subplot(2, 2, 2)
    sns.histplot(df['bits_per_second'] / 1_000_000, kde=True, ax=ax2, color='blue', bins=20)
    ax2.set_title(f'Bandwidth Distribution ({algorithm})', fontsize=14)
    ax2.set_xlabel('Throughput (Mbps)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    
    # 3. RTT over time (if available)
    ax3 = plt.subplot(2, 2, 3)
    if 'rtt' in df and df['rtt'].sum() > 0:
        ax3.plot(df['time_point'], df['rtt'] / 1000, 'g-', linewidth=2)  # Convert to ms
        ax3.set_title(f'Round Trip Time ({algorithm})', fontsize=14)
        ax3.set_xlabel('Time (seconds)', fontsize=12)
        ax3.set_ylabel('RTT (ms)', fontsize=12)
        ax3.grid(True)
    else:
        ax3.text(0.5, 0.5, 'RTT data not available', 
                horizontalalignment='center', verticalalignment='center')
        ax3.set_title('Round Trip Time', fontsize=14)
    
    # 4. Congestion window over time (if available)
    ax4 = plt.subplot(2, 2, 4)
    if 'snd_cwnd' in df and df['snd_cwnd'].sum() > 0:
        ax4.plot(df['time_point'], df['snd_cwnd'] / 1000, 'r-', linewidth=2)  # Convert to KB
        ax4.set_title(f'Congestion Window Size ({algorithm})', fontsize=14)
        ax4.set_xlabel('Time (seconds)', fontsize=12)
        ax4.set_ylabel('cwnd (KB)', fontsize=12)
        ax4.grid(True)
    else:
        ax4.text(0.5, 0.5, 'Congestion window data not available', 
                horizontalalignment='center', verticalalignment='center')
        ax4.set_title('Congestion Window Size', fontsize=14)
    
    # Add a summary text box
    summary_text = '\n'.join([
        f"Algorithm: {algorithm}",
        f"Protocol: {summary.get('protocol', 'N/A')}",
        f"Avg Bandwidth: {summary.get('avg_bandwidth_mbps', 0):.2f} Mbps",
        f"Max Bandwidth: {summary.get('max_bandwidth_mbps', 0):.2f} Mbps",
        f"Min Bandwidth: {summary.get('min_bandwidth_mbps', 0):.2f} Mbps",
        f"Std Dev: {summary.get('std_bandwidth_mbps', 0):.2f} Mbps",
        f"Duration: {summary.get('duration_seconds', 0):.1f} seconds",
    ])
    
    if 'avg_rtt_ms' in summary:
        summary_text += f"\nAvg RTT: {summary['avg_rtt_ms']:.2f} ms"
    
    if 'total_retransmits' in summary:
        summary_text += f"\nTotal Retransmits: {summary['total_retransmits']}"
    
    fig.text(0.5, 0.01, summary_text, ha='center', va='bottom', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.1, 1, 0.95])  # Adjust layout to make room for the summary text
    plt.suptitle(f'BBRv3 Performance Analysis', fontsize=16, y=0.98)
    
    # Save the figure
    plt.savefig(f"{algorithm}_performance_analysis.png", dpi=300, bbox_inches='tight')
    print(f"Visualization saved as {algorithm}_performance_analysis.png")
    
    # Additional analysis: smoothed throughput with moving average
    plt.figure(figsize=(12, 6))
    window_sizes = [1, 5, 10]
    for window in window_sizes:
        smoothed = df['bits_per_second'].rolling(window=window).mean() / 1_000_000
        plt.plot(df['time_point'], smoothed, 
                 label=f'{window}s Moving Avg', 
                 linewidth=2 if window > 1 else 1)
    
    plt.title(f'BBRv3 Throughput with Different Smoothing Windows', fontsize=14)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Throughput (Mbps)', fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{algorithm}_smoothed_throughput.png", dpi=300)
    print(f"Smoothed throughput visualization saved as {algorithm}_smoothed_throughput.png")

    # Create stability analysis
    plt.figure(figsize=(12, 6))
    
    # Calculate coefficient of variation in different time windows
    window_sizes = [10, 30, 60]
    colors = ['blue', 'green', 'red']
    
    for i, window in enumerate(window_sizes):
        if df['time_point'].max() >= window:  # Only if we have enough data
            # Calculate rolling standard deviation and mean
            rolling_std = df['bits_per_second'].rolling(window=window).std() / 1_000_000
            rolling_mean = df['bits_per_second'].rolling(window=window).mean() / 1_000_000
            
            # Calculate coefficient of variation (CV = std/mean)
            cv = rolling_std / rolling_mean
            
            # Plot the CV
            plt.plot(df['time_point'][window-1:], cv[window-1:], 
                     label=f'{window}s Window', color=colors[i], linewidth=2)
    
    plt.title(f'BBRv3 Throughput Stability Analysis', fontsize=14)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Coefficient of Variation', fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{algorithm}_stability_analysis.png", dpi=300)
    print(f"Stability analysis saved as {algorithm}_stability_analysis.png")
    
    plt.close('all')

if __name__ == "__main__":
    file_path = "INDI_reno_results.json"  # Update this to your actual file path
    algorithm = "TCP-Reno"
    
    print(f"Analyzing iperf3 data for {algorithm}...")
    df, summary = analyze_iperf_data(file_path)
    
    if df is not None:
        create_visualizations(df, summary, algorithm)
        print("Analysis complete!")
    else:
        print("Failed to analyze the data.")