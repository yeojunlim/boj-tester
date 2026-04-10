#!/usr/bin/env bash
if [[ -e "/bin/test.py" ]]; then
    read -rp "there is already a file named 'test.py' in /bin. Enter another name: " alt_name
fi

alt_name="${alt_name:-test.py}"
curl -fsSL https://raw.githubusercontent.com/yeojunlim/boj-tester/refs/heads/main/test.py -o "/bin/$alt_name"
chmod +x "/bin/$alt_name"