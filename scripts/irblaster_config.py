#!/usr/bin/python

# A simple script to generate configurations for irblasters

BLASTERS = {
    'office': {
        'address': 'officeir',
        'devices': [
            ('office_tv', 'samsung_tv'),
            ('office_bluray', 'laser_bluray'),
            ('office_aircon', 'daikin_aircon'),
        ]
    },
    'lounge': {
        'address': 'loungeir',
        'devices': [
            ('lounge_tv', 'samsung_tv'),
            ('lounge_bluray', 'laser_bluray'),
            ('lounge_amp', 'denon_avr_891'),
        ]
    },
    'lab': {
        'address': '192.168.1.231',
        'devices': [
            ('lab_aircon', 'carson_aircon'),
            ]
    }
}

for blaster in BLASTERS:
    with open('irblaster_%s.yaml' % blaster, 'w') as out:
        for device, devicetype in BLASTERS[blaster]['devices']:
            with open('%s.codes' % devicetype) as codes:
                for line in codes.readlines():
                    function, code = line.rstrip().split(' ')
                    out.write(
"""%(device)s_%(function)s:
  sequence:
    - service: remote.send_command
      data:
        entity_id: remote.%(address)s_remote
        command:
          - b64:%(code)s

""" % {'device': device,
       'function': function,
       'address': BLASTERS[blaster]['address'],
       'code': code})
