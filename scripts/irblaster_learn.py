#!/usr/bin/python

# A simple script to help with learning codes, with apologies to the
# broadlink team for recycling their code.
#
# Run something like this:
#
# >> workon broadlink
# >> python ./irblaster_learn.py "0x2737 192.168.1.230 32434134ea34"

import base64
import broadlink
import sys
import time


# Work out what device we're connecting to and auth to it
values = sys.argv[1].split()
devicetype = int(values[0],0)
host = values[1]
mac = bytearray.fromhex(values[2])

dev = broadlink.gendevice(devicetype, (host, 80), mac)
dev.auth()

# What is its name (ends up as the name of the code file)
target = raw_input('What target are we programming? ')
with open('%s.codes' % target, 'w+') as f:
    # Read buttons forever
    while True:
        button = raw_input('What button? ')
        dev.enter_learning()
        data = None
        print('Learning...')
        timeout = 30
        while (data is None) and (timeout > 0):
            time.sleep(2)
            timeout -= 2
            data = dev.check_data()
        if data:
            learned = ''.join(format(x, '02x') for x in bytearray(data))
            print('Learned: %s' % learned)
            encoded = base64.b64encode(data).replace('\n', '')
            print('Encoded: %s' % encoded)

            f.write('%s %s\n' %(button, encoded))
        else:
            print('No data received...')
