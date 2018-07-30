#!/bin/bash
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -F
iptables -P INPUT ACCEPT
