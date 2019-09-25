#!/bin/bash

# Variables
ncsrc="/Users/mbrainar/coding/nso-5.1/ncsrc"

while getopts ":nsc" option; do
  case ${option} in
    n ) NSO="true" ;;
    s ) NETSIM="true" ;;
    c ) CLEAN="true" ;;
    \? ) echo "Usage: setup.sh [-n] [-s] [-c]" ;;
  esac
done

# Set source for NSO
echo "Sourcing local NSO"
source $ncsrc

# Start NSO
if [[ $NSO == "true" ]]
then
  make nso
fi

# Start NetSim
if [[ $NETSIM == "true" ]]
then
  make netsim
fi

# Stop/Clean NSO
if [[ $CLEAN == "true" ]]
then
  make clean
fi
