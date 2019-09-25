#!/bin/bash

# Variables
ncsrc="/Users/mbrainar/coding/nso-5.1/ncsrc"

while getopts ":nscl:" option; do
  case ${option} in
    n ) NSO="true" ;;
    s ) NETSIM="true" ;;
    l ) LOAD="true"
        FILE=$OPTARG ;;
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
  set -x #echo on
  ncs-setup --dest . --package cisco-ios-cli-3.8
  ncs
  set +x #echo off
fi

# Start NetSim
if [[ $NETSIM == "true" ]]
then
  set -x #echo on
  ncs-netsim --dir netsim create-device cisco-ios-cli-3.8 core-1
	ncs-netsim --dir netsim add-device cisco-ios-cli-3.8 core-2
	ncs-netsim --dir netsim add-device cisco-ios-cli-3.8 dist-1
	ncs-netsim --dir netsim add-device cisco-ios-cli-3.8 dist-2
	ncs-netsim --dir netsim add-device cisco-ios-cli-3.8 acc-1
	ncs-netsim --dir netsim add-device cisco-ios-cli-3.8 acc-2
	ncs-netsim start
  set +x #echo off
fi

# Load NSO XML file
if [[ $LOAD == "true" ]]
then
  set -x #echo on
  ncs_load -l -m $FILE
  set +x #echo off
fi

# Stop/Clean NSO
if [[ $CLEAN == "true" ]]
then
  set -x #echo on
  ncs --stop
	rm -Rf README.ncs logs/ ncs-cdb/ ncs-java-vm.log ncs-python-vm.log ncs.conf packages/ state/ storedstate target/
  set +x
fi
