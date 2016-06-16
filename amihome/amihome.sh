#!/bin/bash

# Daniel Fernandez Rodriguez <gmail.com daferoes>

# This program will check if a set of IPs are pingable through the network.
# If not, it will start an application until at least one of those IPs 
# become reachable again.

APP=motion
KNOWN_IPS=(192.168.10.11)

PING_INTERVAL=1
PING_PACKETS=5


function ping_ip {
  #echo "Sending $1 $PING_PACKETS packets every "$PING_INTERVAL"s..."
  ping -i $PING_INTERVAL -c $PING_PACKETS $1 > /dev/null 2>&1
}

function kill_app {
  APP=$1
  APP_PID=$(pidof $APP)
  if [ -n "$APP_PID" ]; then
    echo "Stopping $APP ($APP_PID)..."
    kill $APP_PID > /dev/null 2>&1
    wait $APP_PID
  else
    #echo "$APP not running. Nothing to do."
    continue
  fi
}

function start_app {
  APP=$1
  APP_PID=$(pidof $APP)
  if [ -n "$APP_PID" ]; then
    #echo "$APP already running. Nothing to do."
    continue
  else
    echo "Starting $APP..."
    $APP 2> /dev/null &
  fi
}

while true
  do
    AMIHOME=false
    for IP in "${KNOWN_IPS[@]}"; do
      ping_ip $IP
      if [ $? -eq 0 ]; then
        AMIHOME=true
        #echo Founded one device with IP:$IP. Breaking loop
        break
      fi
    done
    if [ $AMIHOME == true ]; then
      PING_INTERVAL=1
      PING_PACKETS=10
      kill_app $APP
    else
      PING_INTERVAL=0.5
      PING_PACKETS=2
      start_app $APP
    fi
  done
