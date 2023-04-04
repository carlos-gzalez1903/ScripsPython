#!/bin/bash
sshpass -p $2 ssh  -o StrictHostKeyChecking=no $1@$3 "$4"


