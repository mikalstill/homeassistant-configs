#!/usr/bin/python

import datetime
import json
import re
import socket
import sys
import time

import paho.mqtt.client as mqtt


TOPIC_SWITCH_RE = re.compile('cmnd/(yurt[0-9]+)/POWER([0-9]+)')
COMMANDS = {
    'software_version': 'Z',
    'relay_states': '[',
    'dc_input_voltage': ']',
    'temperature_as_raw': 'a',
    'temperature_as_string': 'b',
    'relays_all_on': 'd',
    'relay1_on': 'e',
    'relay2_on': 'f',
    'relay3_on': 'g',
    'relay4_on': 'h',
    'relays_all_off': 'n',
    'relay1_off': 'o',
    'relay2_off': 'p',
    'relay3_off': 'q',
    'relay4_off': 'r'
}


with open('/srv/docker/homeassistant/config/helpers/mqtt2yurt.cfg') as f:
    config = json.loads(f.read())


mqttc = mqtt.Client()
last_status = None
devices = {}
sockets = {}


def printresult(lead, data):
    try:
        sys.stdout.write('%s %s\n' %(lead, data))
    except:
        pass

    sys.stdout.write('%s ' % lead)
    for c in data:
        sys.stdout.write('[%d] ' % ord(c))
    sys.stdout.write('\n')
    sys.stdout.flush()


def sendcommand(hostname, command):
    global sockets

    try:
        sockets[hostname].send('b\n')
        printresult('%s %s [socket test] <<' % (datetime.datetime.now(),
                                                hostname),
                    'b')
    except:
        print('%s Rebuilding socket connection to %s'
              %(datetime.datetime.now(), hostname))
        sockets[hostname] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockets[hostname].connect((hostname, 2000))
        sockets[hostname].settimeout(1)

        data = sockets[hostname].recv(2048).rstrip()
        printresult('%s %s [socket test] >>' % (datetime.datetime.now(),
                                                hostname),
                    data)
        sockets[hostname].send('b\n')
        printresult('%s %s [socket test] <<' % (datetime.datetime.now(),
                                                hostname),
                    'b')

    try:
        data = sockets[hostname].recv(2048).rstrip()
        printresult('%s %s [setup] >>' % (datetime.datetime.now(), hostname),
                    data)
    except socket.timeout:
        pass

    sockets[hostname].send('%s\n' % command)
    printresult('%s %s [%s] <<' % (datetime.datetime.now(), hostname, command),
                command)

    try:
        data = sockets[hostname].recv(2048).rstrip()
        printresult('%s %s [%s] >>' % (datetime.datetime.now(), hostname,
                                       command),
                    data)
        return data
    except socket.timeout:
        pass

    return None


def status(hostname):
    global devices
    global mqttc

    print '%s Fetch status for %s' %(datetime.datetime.now(), hostname)

    # The first temperature result is often bogus, so ask until we don't get a
    # b
    temperature = None
    while temperature is None:
        try:
            temperature = sendcommand(device,
                                      COMMANDS['temperature_as_string'])
            temperature = float(temperature)
        except:
            temperature = None

    print('%s Received temperature is %.02f celcius'
          %(datetime.datetime.now(), temperature))
    mqttc.publish('tele/%s/SENSOR' % device, temperature)
    
    for relay in range(1, 5):
        mqttc.publish('tele/%s/POWER%d' %(device, relay),
                      devices[hostname][relay])


def receive(mosq, obj, msg):
    global mqttc

    print '%s Received: %s %s %s' %(datetime.datetime.now(), msg.topic,
                                    str(msg.qos), str(msg.payload))

    m = TOPIC_SWITCH_RE.match(msg.topic)
    if m:
        device = m.group(1)
        relay = int(m.group(2))
        command = msg.payload
        print('    Command for device %s relay %s --> %s'
              %(device, relay, command))

        try:
            if command == 'True':
                sendcommand(device, COMMANDS['relay%s_on' % relay])
                devices[device][relay] = True
            else:
                sendcommand(device, COMMANDS['relay%s_off' % relay])
                devices[device][relay] = False

            status(device)
        except Exception as e:
            print '%s Error: %s' %(datetime.datetime.now(), e)


mqttc.on_message = receive
mqttc.connect(config.get('mqtt_server', 'localhost'),
              config.get('mqtt_port', 1883),
              60)
mqttc.subscribe('cmnd/#', 0)

for device in config['devices']:
    # Reading relay state is buggy, so we just instead turn all the relays off
    # on startup
    print '%s Configure device %s' %(datetime.datetime.now(), device)
    sendcommand(device, COMMANDS['relays_all_off'])
    devices[device] = {}
    for relay in range(1, 5):
        devices[device][relay] = False
    status(device)

last_status = time.time()

while True:
    mqttc.loop(1)
    print '%s ...' % datetime.datetime.now()

    if time.time() - last_status > 29:
        for device in devices:
            status(device)
        last_status = time.time()
