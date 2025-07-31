#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import secrets
import string
import time
import psutil

parser = argparse.ArgumentParser(
    prog = 'vnc_desktop_launcher',
    description = 'noVNC Based Desktop')

parser.add_argument(
    '--username', 
    required=False,
    default='user',
    help='whether the username should be something other than "user"'
)

parser.add_argument(
    '--no-sudo',
    required=False,
    action='store_true',
    help='whether the working user should not have sudo'
)

parser.add_argument(
    '--no-exit-on-failure',
    required=False,
    action='store_true',
    help='whether the docker container should exit or not if something goes wrong and it becomes "UNHEALTHY"'
)

parser.add_argument(
    '--vnc-password-from-env',
    required=False,
    action='store_true',
    help='Whether we set the vnc password from the environment varialble VNC_PASSWORD or whether to randomly generate it'
)

parser.add_argument(
    '--enable-tls',
    required=False,
    action='store_true',
    help='Whether we set the vnc password from the environment varialble VNC_PASSWORD or whether to randomly generate it'
)

args = parser.parse_args()

# Init the environment
# - Add the user
username = args.username
subprocess.run(
    ['/sbin/useradd','-m', '-s','/bin/bash',username],
    capture_output=True,
    check=True
)

# - Grant sudo
if args.no_sudo == False:
    with open('/etc/sudoers.d/%s' % username,'a') as f:
        f.write("%s ALL=(ALL) NOPASSWD: ALL" % username)

# - Configure VNC Password
if args.vnc_password_from_env == False:
    # Randomly generate password
    letter_set = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(letter_set) for i in range(20))

    print("VNC Password = %s" % password)

    with open('/opt/whaletop/vnc_passwd','w') as f:
        f.write(password)

    #! FIXME: needs error handling...
    os.system("mkdir -p /home/%s/.vnc" % username)
    os.system("echo '%s' | vncpasswd -f > /home/%s/.vnc/passwd" % (password, username))
    os.system("chmod 600 /home/%s/.vnc/passwd" % username)

if args.vnc_password_from_env == True:
    #! FIXME: Need to implement it
    raise "VNC_PASSWORD_FROM_ENV NOT IMPLEMENTED"

# - Fix user permissions
#! FIXME: Needs error handling
os.system("chown %s:%s -R /home/%s" % (username,username,username))

#
# Check for /Apps
#
#! FIXME: Need to implement /Apps support
if os.path.isdir('/Apps'):
    print("WARN: Support for /Apps is not implemented yet")

#
# Start the desktop
#

# Report status
with open('/opt/whaletop/status','w') as f:
    f.write("STARTING")

# Remove old log/pid files if user is running a persistent home
os.system("su %s -c 'rm /home/%s/.vnc/*.pid'" % (username,username))
os.system("su %s -c 'rm /home/%s/.vnc/*.log'" % (username,username))

# Set up VNC server & start desktop environment
os.system("su %s -c 'vncserver $DISPLAY -geometry 1280x720 -depth 24'" % username)
os.system("su %s -c 'startlxde &'" % username)

# Capture pid of the vnc server
vnc_home = "/home/%s/.vnc" % username
files = os.listdir(vnc_home)

vncserver_pid = -1

for file in files:
    if file.endswith('.pid'):
        filepath = "%s/%s" % (vnc_home, file)
        with open(filepath, 'r') as f:
            vncserver_pid = int(f.readline().strip())

print("detected vncserver pid of %s" % vncserver_pid)

# Start websockify
if args.enable_tls == False:
    os.system("su %s -c 'websockify --web=/usr/share/novnc/ $NOVNC_PORT localhost:$VNC_PORT &'" % username)
else:
    #! FIXME: implement support for enable-tls
    raise "enable-tls is not implemented"

# Report end of start up sequence
with open('/opt/whaletop/status','w') as f:
    f.write("STARTED")

#! FIXME: Code in some health checking
while True:
    VNC_SERVER_OK = False

    if psutil.pid_exists(vncserver_pid) == True:
        VNC_SERVER_OK = True
        
    
    # Update status file
    if VNC_SERVER_OK == False:
        with open('/opt/whaletop/status','w') as f:
            f.write("UNHEALTHY")
        if args.no_exit_on_failure == False:
            break
    else:
        with open('/opt/whaletop/status','w') as f:
            f.write("HEALTHY")
    
    # Don't do health checks at CPU Freq, that wastes CPU cycles
    time.sleep(1.0)