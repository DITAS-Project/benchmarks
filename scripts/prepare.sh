#!/bin/sh
sudo sysctl -w net.core.somaxconn=40000
sudo sysctl -w net.core.wmem_default=8388608
sudo sysctl -w net.core.rmem_default=8388608
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
sudo sysctl -w net.core.netdev_max_backlog=300000
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=40000
sudo sysctl -w net.ipv4.tcp_sack=1
sudo sysctl -w net.ipv4.tcp_window_scaling=1
sudo sysctl -w net.ipv4.tcp_fin_timeout=15
sudo sysctl -w net.ipv4.tcp_keepalive_intvl=30
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
sudo sysctl -w net.ipv4.tcp_moderate_rcvbuf=1
sudo sysctl -w net.ipv4.tcp_mem='134217728 134217728 134217728'
sudo sysctl -w net.ipv4.tcp_rmem='4096 277750 134217728'
sudo sysctl -w net.ipv4.tcp_wmem='4096 277750 134217728'
sudo sysctl -w net.ipv4.ip_local_port_range='1025 65535'