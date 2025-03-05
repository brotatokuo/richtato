#!/bin/bash

website="richtato.onrender.com"
while true
do
  echo "Pinging $website at $(date)" >> ping_log.txt
  ping -c 4 $website >> ping_log.txt
  sleep 900
done
