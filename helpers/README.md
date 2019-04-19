This directory contains non-standard helpers I have written for homeassistant.
They're kept here just to keep everything together nicely.

mqtt2yurt
=========

I can't really explain why I call my wifi relay boards yurts, the hillarious pun involved is now lost in the mists of time. However, I have relay boards like this -- https://www.ebay.com.au/itm/4-Channel-USB-Wireless-Relay-Bluetooth-WIFI-IOS-Android-Temperature-DS18B20/321150739141?hash=item4ac61362c5:g:MhoAAOxyf~hRyU2U -- that I use with wifi zigbee boards like this -- https://www.ebay.com.au/itm/WiFiBee-WiFi-Module-RN-XV/321213671709?hash=item4ac9d3a91d:g:G5wAAOxyoMxSLTec -- for doing things like turning watering solenoids on and off.

The wifi boards talk TCP on port 2000 with a very simple protocol that is explained in the ebay listing. This helper is a systemd service which acts as a protocol adapter between the mqtt that homeassistant speaks and the protocol the relay boards speak.

An ansible installer is included at mqtt2yurt.yml


python_modern_pip
=================

An set of ansible tasks to ensure we have a modern pip installation. Included
in ansible installers in this directory.