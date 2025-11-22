#!/usr/bin/env bash

# A file for manually sending requests to the sentiment analysis API for
# testing purposes from the terminal.

a=1
while [ $a -gt 0 ]; do
  read -p "Enter query: " query

  if [ "$query" = "q" ]; then
    break
  fi

  payload=$(printf '{"text": "%s"}' "$query")
  curl -X POST "http://localhost:8000/query" \
    -H "Content-Type: application/json" \
    -d "$payload"
    
  echo ""

done

echo "Done!"
