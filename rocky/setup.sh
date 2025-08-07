#!/bin/bash

PUBKEY_FILE="/home/aislab/.ssh/shared_ssh_key/ubuntu_id_rsa.pub"
TARGET_AUTH_KEY_FILE="/home/aislab/.ssh/authorized_keys"

if [ -f "$PUBKEY_FILE" ]; then
    cat "$PUBKEY_FILE" >> "$TARGET_AUTH_KEY_FILE"
    chown -R aislab:aislab /home/aislab/.ssh
    chmod 600 "$TARGET_AUTH_KEY_FILE"
fi

# start sshd
exec /usr/sbin/sshd -D -e -o ListenAddress=0.0.0.0
