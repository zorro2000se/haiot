#!/bin/bash
#kill $(cat /var/run/thd.pid)
#find events: thd --dump /dev/input/by-id/*
echo Starting THD
echo Stop existing THD
killall -q thd
echo Run THD daemon
/usr/sbin/thd --triggers /etc/triggerhappy/triggers.conf --socket /var/run/thd.socket  --pidfile /var/run/thd.pid  --daemon
echo Adding THD living
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag living --add  /dev/input/by-id/usb-Microsoft_Microsoft®_2.4GHz_Transceiver_v8.0-event-kbd
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag living --add /dev/input/by-id/usb-Microsoft_Microsoft®_2.4GHz_Transceiver_v8.0-if01-event-mouse
#to catch KEY_CALC for kodi
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag living --add /dev/input/by-id/usb-Microsoft_Microsoft®_2.4GHz_Transceiver_v8.0-if02-event-joystick
echo Adding THD bucatarie
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag bucatarie --add /dev/input/by-id/usb-CHESEN_USB_Keyboard-event-kbd
echo Adding THD baie
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag baie --add /dev/input/by-id/usb-Cyp_Se_WitheHome-event-mouse
echo Adding THD dormitor
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag dormitor --add /dev/input/by-id/usb-12c9_2.4GHz_2way_RF_Receiver-event-mouse
echo Adding THD beci
/usr/sbin/th-cmd  --socket /var/run/thd.socket --tag beci --add /dev/input/by-id/usb-MOSART_Semi._2.4G_Wireless_Mouse-event-mouse
echo Initialise all outputs
/home/dcristian/PYC/scripts/audio/mpc-play.sh 6600 init
/home/dcristian/PYC/scripts/audio/mpc-play.sh 6601 init
/home/dcristian/PYC/scripts/audio/mpc-play.sh 6602 init
/home/dcristian/PYC/scripts/audio/mpc-play.sh 6603 init
/home/dcristian/PYC/scripts/audio/mpc-play.sh 6604 init
