#!/bin/bash

# Define the line to add
HIST_LINE='export HISTFILE=~/.bash_history.$(tty | sed "s:/dev/::")'

# 1. Add to /etc/bash.bashrc (system-wide for all interactive shells)
if ! grep -Fxq "$HIST_LINE" /etc/bash.bashrc; then
    echo "$HIST_LINE" >> /etc/bash.bashrc
    echo "[+] Added HISTFILE export to /etc/bash.bashrc"
else
    echo "[=] HISTFILE already set in /etc/bash.bashrc"
fi

# 2. (Optional) Update existing user ~/.bashrc files
echo
read -p "Do you want to update all existing users' ~/.bashrc files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    for home in /home/* /root; do
        user_bashrc="$home/.bashrc"
        if [ -f "$user_bashrc" ]; then
            if ! grep -Fxq "$HIST_LINE" "$user_bashrc"; then
                echo "$HIST_LINE" >> "$user_bashrc"
                echo "[+] Added to $user_bashrc"
            else
                echo "[=] Already set in $user_bashrc"
            fi
        fi
    done
fi

echo "Per-TTY HISTFILE setup complete."
