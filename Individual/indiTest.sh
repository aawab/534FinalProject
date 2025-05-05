#!/bin/bash
# INDIVIDUAL TESTING

# Var for cc algo
ALGORITHM=cubic 

# Set wanted cc algo
sudo sysctl -w net.ipv4.tcp_congestion_control=$ALGORITHM

# Check to ensure correct cc algo
sysctl net.ipv4.tcp_congestion_control

# Run for 180 seconds
echo "Testing $ALGORITHM"
iperf3 -c 192.168.120.128 -t 180 -i 1 -J > "INDI_${ALGORITHM}_results.json"

# Write to output file
echo "Finished testing."
cat "INDI_${ALGORITHM}_results.json"
