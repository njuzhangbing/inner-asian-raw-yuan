#!/bin/bash
BUA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
U="https://upload.wikimedia.org/wikipedia/commons/6/66/DiezAlbumsFallOfBaghdad.jpg"
cd ~/Downloads/mongol-yuan-dress
for i in $(seq 1 40); do
  code=$(curl -s -A "$BUA" -H "Referer: https://commons.wikimedia.org/" --max-time 40 -o /dev/null -w "%{http_code}" "$U")
  echo "$(date +%H:%M:%S) probe#$i -> HTTP $code"
  if [ "$code" = "200" ]; then
    echo "冷却解除，开始下载"
    exec python3 tools/commons_dl.py _logs/cat_index 01_images/commons
  fi
  sleep 90
done
echo "40 次探测仍被限流，放弃"
