#!/bin/bash  
sudo mn -c 
sudo mn --custom mininet/$1.py --topo $1 --switch ovsk --controller remote --mac 
