#!/bin/bash

# Daniel Fernandez Rodriguez <gmail.com daferoes>

# This script will check if a certain IP is pingable through the network.
# If not, it will start an application until that IP is reachable again.

APP=motion
IP_ADDRESS=192.168.1.11

while true; do
  ping -c 2 $IP_ADDRESS > /dev/null
  if [ $? -eq 0 ]; then
    APP_PID=$(pidof $APP)
      if [ -n "$APP_PID" ]; then
        echo "Stopping $APP ($APP_PID)..."
        kill $APP_PID > /dev/null
        wait $APP_PID
      else
        echo "Device detected and $APP not running. Nothing to do."
      fi
  else
    echo "Device not detected. Starting $APP..."
    APP_PID=$(pidof $APP)
      if [ -n "$APP_PID" ]; then
        echo "$APP is already running. Nothing to do."
      else
        echo "Starting $APP..."
        $APP & > /dev/null
      fi
  fi
done
