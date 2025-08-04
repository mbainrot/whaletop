#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import secrets
import string
import time
import psutil
import shutil

from OpenSSL import crypto, SSL

# Parse arguments
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
    help='Whether to enable TLS at all, if specified without --tls-certifcate will automatically generate a self-signed certificate.'
)

parser.add_argument(
    '--tls-certificate',
    required=False,
    default=None,
    help='All in one pem formatted certificate to be used by websockify.'
)

args = parser.parse_args()

def certificateIsExpired(path):
    '''
    Tests the provided path certificate to see whether it's expired

    Returns False if not expired, returns True if expired
    '''

    if os.path.exists(path) == False:
        raise Exception("'%s' does not exist" % path)

    x509_cert = None
    with open(path, 'rt') as f:
        x509_cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read(-1))

    now = time.time()
    x509exp_ts = x509_cert.get_notAfter()
    expts = time.mktime(time.strptime(x509exp_ts.decode('ASCII'), '%Y%m%d%H%M%SZ'))

    if now > expts:
        return True
    
    return False

def getPassword():
    return '';

def pemIsPassworded(path):
    '''
    Tests whether the private key in a given pem file has a password on it
    '''
    if os.path.exists(path) == False:
        raise Exception("'%s' does not exist" % path)
    
    
    pemContent = None
    with open(path, 'rt') as f:
        pemContent = f.read(-1)
    
    foundEncrypted = False

    try:
        pemContent.index('ENCRYPTED')
        return True
    except:
        print("String ENCRYPTED not found in pemContent")
  

    pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, pemContent)

    if pkey == None:
        raise Exception("Got None for pkey, something has gone wrong loading the certificate")

    pkeyCheck = pkey.check()
    print("pkey.check() == %s" % pkeyCheck)

    if pkeyCheck == False:
        raise Exception("Private key failed validation")

    return False

def autoCopyDesktopFiles(path):
    files = os.listdir(path)
    for file in files:
        fullpath = "/%s/%s" % (path, file)
        dstPath = "/usr/share/applications/%s" % file

        if fullpath.endswith(".desktop") and os.path.isfile(fullpath):
            shutil.copy(fullpath, dstPath)
        elif os.path.isdir(fullpath):
            autoCopyDesktopFiles(fullpath)

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
password = None
if args.vnc_password_from_env == False:
    # Randomly generate password
    letter_set = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(letter_set) for i in range(20))
else:
    if not "VNC_PASSWORD" in os.environ:
        raise Exception("Environment variable VNC_PASSWORD is not defined!")

    password = os.environ["VNC_PASSWORD"]

if password == None:
    raise Exception("Failed to aquire a password for VNC")

if password == '':
    raise Exception("Password must not be blank")

print("VNC Password = %s" % password)

with open('/opt/whaletop/vnc_passwd','w') as f:
    f.write(password)

vncHome = "/home/%s/.vnc" % username
passwdFile = "%s/passwd" % vncHome

os.system("mkdir -p %s" % vncHome)

if os.path.exists(vncHome) == False:
    raise Exception("Failed to create %s" % vncHome)

os.system("echo '%s' | vncpasswd -f > %s" % (password, passwdFile))

if os.path.exists(passwdFile) == False:
    raise Exception("Failed to set passwd file @ %s" % passwdFile)

# Set permissions of the passwd file to 600 by just providing S_IRUSR (which is read by owner)
# at time of writing this blanks all other permissions out
os.chmod(passwdFile, os.path.stat.S_IRUSR)

passwdFileStat = os.stat(passwdFile)

if passwdFileStat.st_mode != 33024:
    raise Exception("Incorrect permissions on %s (got %s, expected 33024)" % (passwdFile, passwdFileStat.st_mode))

if args.tls_certificate != None and args.enable_tls == False:
    # User forgot to set --enable-tls, lets be helpful and enable it
    args.enable_tls = True

if args.enable_tls == True:
    if args.tls_certificate == None:
        pemPath = "/home/%s/.vnc/tls.pem" % username
        pubPemPath = "/opt/whaletop/pub_ssl.pem"

        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 4096)

        cert = crypto.X509()
        cert.get_subject().C = 'AU'
        cert.get_subject().ST = 'ACT'
        cert.get_subject().L = 'Canberra'
        cert.get_subject().O = 'Non-existant Company'
        cert.get_subject().OU = 'Gadgets and Widgets Unit'
        cert.get_subject().CN = 'localhost.localdomain'
        cert.get_subject().emailAddress = 'null@localhost.local.domain'
        cert.set_serial_number(0)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(3600 * 24 * 365)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha512')

        # Dump public certificate
        with open(pemPath, 'wt') as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

        # Dump public cert in /opt
        with open(pubPemPath, 'wt') as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))       

        # Dump private key
        with open(pemPath, 'at') as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))

    if args.tls_certificate != None:
        pemPath = args.tls_certificate
        # Check that certificate file exists in container
        if os.path.exists(pemPath) == False:
            raise Exception("Certificate file %s does not exist" % pemPath)
        
        # Check that certificate _is not expired_
        certExpired = certificateIsExpired(pemPath)

        if certExpired == True:
            raise Exception("Certificate is expired, refusing to start the server")

        pemPassworded = pemIsPassworded(pemPath)

        print("pemPassworded == %s" % pemPassworded)

        if pemPassworded == True:
            raise Exception("Private key has a password and we don't support that yet")

        # If we got to here without failure, all is well
        os.system("cp '%s' /home/%s/.vnc/tls.pem" % (pemPath, username))

# - Fix user permissions
#! FIXME: Needs error handling & not using os.system
os.system("chown %s:%s -R /home/%s" % (username,username,username))

#
# Check for /Apps
#
if os.path.isdir('/Apps'):
    autoCopyDesktopFiles('/Apps')

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
    pemPath = "/home/%s/.vnc/tls.pem" % username

    if os.path.exists(pemPath) == False:
        raise Exception("%s certificate does not exist")
    
    os.system("su %s -c 'websockify --web=/usr/share/novnc/ --cert='%s' --key='%s' --ssl-only $NOVNC_PORT localhost:$VNC_PORT &'" % (username, pemPath, pemPath))


# Report end of start up sequence
with open('/opt/whaletop/status','w') as f:
    f.write("STARTED")

while True:
    VNC_SERVER_OK = False
    CERTIFICATE_OK = False

    # Check that VNC server is still running
    if psutil.pid_exists(vncserver_pid) == True:
        VNC_SERVER_OK = True
    
    # Check that certificate hasn't expired
    if args.enable_tls == True:
        pemPath = "/home/%s/.vnc/tls.pem" % username
        if certificateIsExpired(pemPath) == False:
            CERTIFICATE_OK = True
        else:
            print("ERROR: Certificate has expired")
    
    # Update status file
    if VNC_SERVER_OK == False or (CERTIFICATE_OK == False and args.enable_tls == True):
        with open('/opt/whaletop/status','w') as f:
            f.write("UNHEALTHY")
        if args.no_exit_on_failure == False:
            break
    else:
        with open('/opt/whaletop/status','w') as f:
            f.write("HEALTHY")
    
    # Don't do health checks at CPU Freq, that wastes CPU cycles
    time.sleep(1.0)