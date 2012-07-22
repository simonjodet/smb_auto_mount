#!/usr/bin/python -O

"""
smb_auto_mount:
Mac OS 10.7 utility to mount Samba shares when connected on a specific Wifi network.
It will try to unmount those shares if you're not on the Wifi network.

Usage:
Edit the conf dictionary below to set your configuration for one or more Wifi networks and with one or more shares for each network.
I guess it can be "croned" with a small interval. After all, it doesn't do much and Python is supposed to be a fast language, right?


Copyright (c)2012 Simon Jodet

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

conf = [
        {
        'wifi_SSID': 'Your Wifi network\'s SSID',
        'shares': [
                {
                'smb_user': 'smb_server_username',
                'smb_pwd': 'smb_server_password',
                'smb_host': 'smb_server_hostname', # localhost works too (but that's silly ^), IP addresses should work too but not tested
                'smb_folder': 'smb_server_shared_folder_to_mount', # no leading or trailing slashes please
                'mount_path': '/where/to/mount/the/shared/folder', # the path will be created if it does not exist yet,
                'debug': 'False' # optional, boolean, default is False, True will let mount errors go through so you can debug them
            }
        ]
    }
]

debug = False # set this to True to know what network SSID is found by the script

from subprocess import *
import re
import os

class smb_auto_mount():
    """
    Utility to mount Samba shares when connected on a specific Wifi network
    """

    def __init__(self, conf, debug=False):
        """
        Will return success message if share mount succeeded
        Will return failure message if share mount failed
        WIll return nothing if everything is already mounted
        """
        self.devnull = devnull = open('/dev/null', 'w')
        current_mounts = check_output(['mount'])
        current_network = self.getWifiSSID()
        match_found = False
        for network in conf:
            if network['wifi_SSID'] == current_network:
                match_found = True
                for share in network['shares']:
                    mount_description = '//' + share['smb_user'] + '@' + share['smb_host'] + '/' + share['smb_folder'] + ' on ' + os.path.realpath(share['mount_path'])
                    if mount_description not in current_mounts: # Don't want to mount if already mounted
                        if not os.path.exists(share['mount_path']):
                            os.makedirs(share['mount_path'])
                        debug = False
                        if('debug' in share):
                            debug = share['debug']
                        mount = self.mount(share['smb_user'], share['smb_pwd'], share['smb_host'], share['smb_folder'],
                            share['mount_path'], debug)
                        if (mount != 0): # Something went wrong when trying to mount the shared drive
                            print 'WARNING: Could not mount ' + '//' + share['smb_user'] + '@' + share['smb_host'] + '/' + share['smb_folder'] + ' on ' + share['mount_path']
                        else:
                            print 'Mounted ' + '//' + share['smb_user'] + '@' + share['smb_host'] + '/' + share['smb_folder'] + ' on ' + os.path.realpath(share['mount_path'])
            else:
                for share in network['shares']:
                    call(['umount', share['mount_path']], stdout=self.devnull, stderr=self.devnull)

            if not match_found and debug:
                print 'No configuration set for the "' + current_network + '" network'

    def getWifiSSID(self):
        """
        Tries to guess your wifi network SSID
        """
        output = check_output(
            ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
            stderr=self.devnull)
        regex = re.search('^\s*SSID: (.*)', output, flags=re.MULTILINE)
        if regex is None: #Avoiding calling group method on non-MatchObject object
            return False
        return regex.group(1)

    def mount(self, smb_user, smb_pwd, smb_host, smb_folder, mount_path, debug):
        """
        Tries to mount a Samba share on the given mount path
        """
        if debug:
            stderr_target = None
        else:
            stderr_target = self.devnull
        return call(
            ['mount', '-t', 'smbfs', '//' + smb_user + ':' + smb_pwd + '@' + smb_host + '/' + smb_folder, mount_path],
            stdout=self.devnull, stderr=stderr_target)

smb_auto_mount(conf, debug)