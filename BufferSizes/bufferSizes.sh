#!/bin/bash
# INTRA PROTOCOL BUFFER SIZE TESTING

# Var for cc algo
ALGORITHM=$1 
routerIf="ens33"

# Define sender IPs
sender1IP="192.168.139.128" 
sender2IP="192.168.139.129"
sender3IP="192.168.139.130"

senderArr=($sender1IP $sender2IP $sender3IP)

receiver1IP="192.168.192.128"
receiver2IP="192.168.192.129"
receiver3IP="192.168.192.130"

receiverArr=($receiver1IP $receiver2IP $receiver3IP)

# Test different buffer sizes (in KB)

for bufferSize in 12 25 50 100 200; do
  echo "Testing $ALGORITHM with buffer size ${bufferSize}KB"
  
  # Configure buffer size
  sudo tc qdisc del dev $routerIf root 2>/dev/null
  sudo tc qdisc add dev $routerIf root handle 1: htb default 12
  sudo tc class add dev $routerIf parent 1: classid 1:1 htb rate 10mbit ceil 10mbit
  sudo tc qdisc add dev $routerIf parent 1:1 handle 10: netem delay 20ms
  sudo tc qdisc add dev $routerIf parent 10:1 handle 100: bfifo limit ${bufferSize}kb
  
  # Set congestion control ALGORITHM on all senders
  for i in ${!senderArr[@]}; do
    echo "ubuntu" | ssh ${senderArr[$i]} "sudo -S sysctl -w net.ipv4.tcp_congestion_control=$ALGORITHM"
  done
  
  # Run tests
  for i in ${!senderArr[@]}; do
    ssh ${senderArr[$i]} "iperf3 -c ${receiverArr[$i]} -t 60 -i 1 -J > ${sender}_${ALGORITHM}_buffer${bufferSize}_results.json" &
  done
  
  wait
  
  echo "Intra-protocol buffer size ${bufferSize}KB test complete"
done