#!/bin/bash
set -e

# Start redbot1
(
  source /home/rej1/lavalink/redbot1/venv/bin/activate
  exec python -m redbot redbot1 >> /home/rej1/lavalink/redbot1/redbot1.log 2>&1
) &

# Start redbot2
(
  source /home/rej1/lavalink/redbot2/venv/bin/activate
  exec python -m redbot redbot2 >> /home/rej1/lavalink/redbot2/redbot2.log 2>&1
) &

# Start redbot3
(
  source /home/rej1/lavalink/redbot3/venv/bin/activate
  exec python -m redbot redbot3 >> /home/rej1/lavalink/redbot3/redbot3.log 2>&1
) &

wait
