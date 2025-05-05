import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def preprocess():
    dataList = []
    jsonFiles = glob.glob('*.json')
    
    for path in jsonFiles:
        with open(path, 'r') as f:
            try:
                data = json.load(f)
                parts = path.split('_')
                protocol = parts[1]
                bufferSize = int(parts[2].replace('kb', ''))
                
                bitsPerSecond = data['end']['streams'][0]['sender']['bits_per_second']
                retransmits = data['end']['streams'][0]['sender'].get('retransmits', 0)
                flow = data['start'].get('test_start', {}).get('flow_id', 1)
                
                dataList.append({
                    'protocol': protocol,
                    'bufferSize': bufferSize,
                    'flow': flow,
                    'throughputMbps': bitsPerSecond / 1e6,
                    'retransmits': retransmits
                })
            except Exception as e:
                print(f"Error processing {path}: {str(e)}")
    
    return pd.DataFrame(dataList)

def makeViz(df):
    sns.set_theme(style="whitegrid")
    colors = sns.color_palette("husl", n_colors=len(df['protocol'].unique()))
    
    def plotThroughputDist():
        plt.figure(figsize=(12, 6))
        sns.boxplot(x='protocol', y='throughputMbps', data=df, palette=colors)
        plt.title('Throughput Distribution by Protocol\nConcurrent Flow Testing')
        plt.xlabel('Congestion Control Protocol')
        plt.ylabel('Throughput (Mbps)')
        plt.xticks(rotation=45)
        plt.savefig('throughput_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plotProtocolPerformance():
        _, ax = plt.subplots(figsize=(12, 6))

        for idx, protocol in enumerate(df['protocol'].unique()):
            protocolData = df[df['protocol'] == protocol]
            meanThroughput = protocolData.groupby('bufferSize')['throughputMbps'].mean()
            ax.plot(meanThroughput.index, meanThroughput.values, marker='o', 
                   label=protocol, color=colors[idx], linewidth=2)
        
        ax.set_title('Protocol Performance vs Buffer Size\nShared Network Environment')
        ax.set_xlabel('Buffer Size (KB)')
        ax.set_ylabel('Average Throughput (Mbps)')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        plt.savefig('throughput_vs_buffersize.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plotHeatmap():
        pivotData = df.pivot_table(values='throughputMbps', index='protocol',
                                 columns='bufferSize', aggfunc='mean')
        _, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivotData, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                   cbar_kws={'label': 'Throughput (Mbps)'})
        ax.set_title('Protocol Performance Heatmap\nThroughput vs Buffer Size')
        plt.savefig('performance_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plotFairnessIndex():
        def calcJainsFairness(throughputs):
            n = len(throughputs)
            return (sum(throughputs) ** 2) / (n * sum(x ** 2 for x in throughputs)) if n else 0
        
        fairnessData = []
        bufferSizes = sorted(df['bufferSize'].unique())
        
        for buffer in bufferSizes:
            bufferData = df[df['bufferSize'] == buffer]
            throughputs = [group['throughputMbps'].mean() 
                         for _, group in bufferData.groupby('protocol')]
            fairnessData.append({
                'bufferSize': buffer,
                'fairnessIndex': calcJainsFairness(throughputs)
            })
        
        fairnessDf = pd.DataFrame(fairnessData)
        _, ax = plt.subplots(figsize=(12, 6))
        barColors = ['#2ecc71', '#3498db', '#9b59b6']
        bars = ax.bar(range(len(bufferSizes)), fairnessDf['fairnessIndex'],
                     color=[barColors[i % len(barColors)] for i in range(len(bufferSizes))])
        
        ax.set_xlabel('Buffer Size (KB)', fontsize=12)
        ax.set_ylabel("Jain's Fairness Index", fontsize=12)
        ax.set_title("Network Fairness Analysis\nHigher is Better (1.0 = Perfect Fairness)")
        ax.set_xticks(range(len(bufferSizes)))
        ax.set_xticklabels(bufferSizes)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height, f'{height:.3f}',
                   ha='center', va='bottom')
        
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_ylim(0, 1.0)
        ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, 
                   label='Perfect Fairness (1.0)')
        ax.legend()
        
        plt.savefig('fairness_index.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plotThroughputShare():
        for buffer in df['bufferSize'].unique():
            bufferData = df[df['bufferSize'] == buffer]
            plt.figure(figsize=(10, 6))
            totalThroughput = bufferData.groupby('protocol')['throughputMbps'].mean()
            plt.pie(totalThroughput, labels=totalThroughput.index, autopct='%1.1f%%',
                   colors=colors)
            plt.title(f'Throughput Share (Buffer: {buffer}KB)')
            plt.savefig(f'throughput_share_{buffer}kb.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    plotThroughputDist()
    plotProtocolPerformance()
    plotHeatmap()
    plotFairnessIndex()
    plotThroughputShare()

if __name__ == "__main__":
    df = preprocess()
    makeViz(df)