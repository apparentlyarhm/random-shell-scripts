#! /bin/bash

output=$(rdmsr 0x198 -u --bitfield 47:32) || exit
voltage=$(echo "scale=2; $output/8192" | bc)
echo "${voltage} V"
