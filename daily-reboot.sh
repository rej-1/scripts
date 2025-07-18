#!/bin/bash

# Send warning to Minecraft players
sudo -u mcserver tmux send-keys -t atm10 "say Server initializing daily restart in 1 minute. Please reconnect in 2 minutes." C-m
sleep 60
sudo -u mcserver tmux send-keys -t atm10 "say Server restarting in 3 seconds!" C-m
sleep 3
sudo -u mcserver tmux send-keys -t atm10 "stop" C-m


# Wait for Minecraft server to fully stop
sleep 10
 
# Reboot the server
sudo /usr/bin/systemctl reboot
