#!/bin/bash

BACKUP_ROOT="/mnt/sata/backups/atm10"
SRC="/home/mcserver/atm10"
TODAY=$(date '+%Y-%m-%d')
DAYOFMONTH=$(date '+%d')
MONTH=$(date '+%m')
YEAR=$(date '+%Y')

mkdir -p "$BACKUP_ROOT/daily" "$BACKUP_ROOT/monthly" "$BACKUP_ROOT/yearly"

# Notify players backup is starting
sudo -u mcserver tmux send-keys -t atm10 "say Server initializing daily backup." C-m

# Make today's backup
rsync -a --delete "$SRC/" "$BACKUP_ROOT/daily/$TODAY/"

# If it's the 1st of the month, copy to monthly (overwrite if exists)
if [ "$DAYOFMONTH" = "01" ]; then
    rm -rf "$BACKUP_ROOT/monthly/${YEAR}-${MONTH}-01"
    cp -al "$BACKUP_ROOT/daily/$TODAY" "$BACKUP_ROOT/monthly/${YEAR}-${MONTH}-01"
fi

# If it's January 1st, copy to yearly (overwrite if exists)
if [ "$DAYOFMONTH" = "01" ] && [ "$MONTH" = "01" ]; then
    rm -rf "$BACKUP_ROOT/yearly/${YEAR}-01-01"
    cp -al "$BACKUP_ROOT/daily/$TODAY" "$BACKUP_ROOT/yearly/${YEAR}-01-01"
fi

# Prune: keep only 7 daily, 1 monthly (latest), 1 yearly (latest)
ls -1dt $BACKUP_ROOT/daily/* | tail -n +8 | xargs rm -rf
ls -1dt $BACKUP_ROOT/monthly/* | tail -n +2 | xargs rm -rf
ls -1dt $BACKUP_ROOT/yearly/* | tail -n +2 | xargs rm -rf

# Notify players backup is complete
sudo -u mcserver tmux send-keys -t atm10 "say Daily server backup is complete!" C-m
