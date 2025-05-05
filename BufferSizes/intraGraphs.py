import json
import os
import matplotlib.pyplot as plt
import numpy as np
import glob

def preprocess(filename):
    with open(filename) as f:
        data = json.load(f)
    
    intervals = data.get('intervals', [])
    throughput, retransmits, rtt = [], [], []
    
    for interval in intervals:
        sumData = interval.get('sum', {})
        throughput.append(sumData.get('bits_per_second', 0) / 1e6)  # to Mbps
        retransmits.append(sumData.get('retransmits', 0))
        
        tcpInfo = sumData.get('tcp_info', {})
        rtt.append(tcpInfo.get('rtt', 0) / 1000 if tcpInfo else 0)  # to ms
    
    return {
        'throughput': throughput,
        'retransmits': retransmits,
        'rtt': rtt,
        'avgThroughput': np.mean(throughput) if throughput else 0,
        'totalRetransmits': sum(retransmits),
        'avgRtt': np.mean(rtt) if rtt else 0
    }

def plotThroughputByBuffer(dataFolder="Files", outFile="throughput_by_algo_sender_buffer.png"):
    results = {}
    files = glob.glob(os.path.join(dataFolder, "*_*_buffer*_results.json"))
    
    if not files:
        print(f"No results in {dataFolder}")
        return
        
    ips, algos, bufferSizes = set(), set(), set()

    for file in files:
        fname = os.path.basename(file)
        ip, algo, bufferPart = fname.split('_')[:3]
        bufferSize = int(''.join(filter(str.isdigit, bufferPart)))

        ips.add(ip)
        algos.add(algo)
        bufferSizes.add(bufferSize)

        results.setdefault(algo, {}).setdefault(ip, {})[bufferSize] = preprocess(file)['avgThroughput']

    sortedIps = sorted(ips)
    sortedAlgos = sorted(algos)
    sortedBuffers = sorted(bufferSizes)
    
    senderLabels = {ip: f"Sender {i+1}" for i, ip in enumerate(sortedIps)}
    _, axes = plt.subplots(len(sortedAlgos), 1, figsize=(12, 6 * len(sortedAlgos)))
    
    x = np.arange(len(sortedBuffers))
    width = 0.8 / len(sortedIps)

    for i, algo in enumerate(sortedAlgos):
        ax = axes[i, 0] if len(sortedAlgos) > 1 else axes
        
        for j, ip in enumerate(sortedIps):
            throughputs = [results[algo][ip].get(bs, 0) for bs in sortedBuffers]
            offset = (j - (len(sortedIps) - 1) / 2) * width
            bars = ax.bar(x + offset, throughputs, width, label=senderLabels[ip])
            ax.bar_label(bars, fmt='%.1f', fontsize=8)

        ax.set_ylabel('Avg Throughput (Mbps)')
        ax.set_title(f'{algo} - Throughput vs Buffer Size')
        ax.set_xticks(x, [f"{bs}KB" for bs in sortedBuffers])
        ax.set_xlabel('Buffer Size (KB)')
        ax.legend(title="Sender")
        ax.grid(True, axis='y', linestyle='--')

    plt.tight_layout()
    plt.savefig(outFile)

def plotThroughputBySender(dataFolder="Files", outFile="throughput_by_sender.png"):
    results = {}
    files = [f for f in glob.glob(os.path.join(dataFolder, "*_*_results.json")) 
             if '_buffer' not in f]

    if not files:
        print(f"No results in {dataFolder}")
        return

    for file in files:
        senderId, algo = os.path.basename(file).replace('_results.json', '').split('_')
        metrics = preprocess(file)
        results.setdefault(algo, {})[senderId] = metrics['avgThroughput']

    sortedAlgos = sorted(results.keys())
    rttLabels = ["1/2*baseRTT", "1*baseRTT", "2*baseRTT"]
    
    _, axes = plt.subplots(len(sortedAlgos), 1, figsize=(10, 5 * len(sortedAlgos)))
    x = np.arange(len(rttLabels))

    for i, algo in enumerate(sortedAlgos):
        ax = axes[i, 0] if len(sortedAlgos) > 1 else axes
        throughputs = [results[algo].get(str(j), 0) for j in range(len(rttLabels))]
        bars = ax.bar(x, throughputs)
        ax.bar_label(bars, fmt='%.1f', fontsize=9)
        
        ax.set_ylabel('Avg Throughput (Mbps)')
        ax.set_title(f'{algo} - Throughput per Sender')
        ax.set_xticks(x, rttLabels)
        ax.set_xlabel('RTT Ratio')
        ax.grid(True, axis='y', linestyle='--')

    plt.tight_layout()
    plt.savefig(outFile)

if __name__ == "__main__":
    plotThroughputByBuffer()
    plotThroughputBySender()