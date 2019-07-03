#!/usr/bin/python

# A simple script to generate configurations for irblasters

BLASTERS = {
    'office': {
        'address': '192.168.1.230',
        'devices': [
            ('office_tv', 'samsung_tv'),
            ('office_bluray', 'laser_bluray'),
            ('office_aircon', 'daikin_aircon'),
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
    - service: broadlink.send
      data:
        host: %(address)s
        packet:
          - '%(code)s'

""" % {'device': device,
       'function': function,
       'address': BLASTERS[blaster]['address'],
       'code': code})
