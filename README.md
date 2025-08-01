# Whaletop
Docker + noVNC + LXDE Based Desktop.

> [!IMPORTANT]
> Support for this repository is best effort due to me working full time. I will try my best where I can to address issues in a timely manner where my other commitments allow. This may result in some neglect of this repository from time to time.

## Basic Usage
To get started quickly you can run the following command, note depending on your docker configuration and your user's group membership you may need to prepend this with `sudo`
```
docker run -it --rm -p 8080:8080 mbainrot/whaletop
```

Once the container has started you can access the session with the password that is logged in the STDOUT by navigating your web browser to http://localhost:8080

Alternatively you can find the password in the container's file system under `/opt/whaletop/vnc_passwd`.

## Session preservation
By default without any special parameters and using the above example run command, your desktop will be emphemeral which means you will loose everything when the container is stopped.

To prevent this we recommend mounting the home volume to either a docker volume or local directory on the docker host

An example commandline of how to do this and with support for chromium sandboxing is as follows
```
docker run -it --rm --security-opt seccomp=$(pwd)/chrome.json -v /home/$USER/Docker/Volumes/user:/home/user -p 8080:8090 mbainrot/whaletop
```

Explaination of the parameters:
* `-it --rm` - This makes the session interactive and also sets it to clean up on exit
* `--security-opt seccomp=$(pwd)/chrome.json` - tells the docker engine to use the chrome.json security policy to enable the required priviledged functionality to be able to sandbox processes
* `-v /home/$USER/Docker/Volumes/user:/home/user` - tells the docker engine to mount the host side directory `/home/$USER/Docker/Volumes/user` in the container as `/home/user` which is the default user's home directory.
* `-p 8080:8090` - tells the docker engine to expose the noVNC server outside of the container on port 8090

## Orchestation Features
To make this container more versitile I have incorporated functionality to make scripting/automation a lot easier.

You can either use `docker exec` to retrieve these, or volume mounting to expose them in the host system.

### Retrieval of the generated VNC password
The plaintext version of the VNC password can be found in the container at `/opt/whaletop/vnc_passwd`

### Retrieval of the container's health
Whilst not fully implemented yet the health status of the container can be found in the container at `/opt/whaletop/status`

The valid statuses are as follows:
* STARTING - This is set just before the start.py script attempts to start the X Server and VNC
* STARTED - This fires just after all the system calls are completed but before the health checks start
* HEALTHY - This is fired after the health checks complete for the first time

## Start.py Parameters
The following parameters are supported in the `/start.py` allowing further behavour customisation.

To use the parameters add to the end of the commandline `/start.py --your-params-here`

e.g.
```
docker run -it --rm -p 8080:8080 mbainrot/whaletop /start.py --username=bob
```

### --username (default == user)
Specifies what the name of the user's session user should be. Useful for further customising the user's experience.

### --no-sudo
By default the start.py grants the user sudo access to the VM. If this is undesirable you can prevent this by setting the --no-sudo switch.

### --vnc-password-from-env
Allows the presetting of the VNC password from the environment variable `VNC_PASSWORD`, useful for managed user sessions where you are automating the VNC connection.

Example invocation:
```
docker run -it --rm -p 8080:8080 --env VNC_PASSWORD=$VNC_PASSWORD mbainrot/whaletop /start.py --vnc-password-from-env
```

### --enable-tls
Enables SSL on the noVNC page for improved security. By default it adds `--ssl-only` to the websockify commandline. Will auto generate self-signed certificate if `--tls-certificate` is absent. Certificate is valid for 1 year and is generated with example parameters. If you want a nicer cert, generate your own and use `--tls-certificate`

For trust verification purposes a copy of the public self-signed cert is provided in `/opt/whaletop/pub_ssl.pem`

### --tls-certificate
Specifies the path to the SSL certificates to be used by websockify.

Certificate should be a combined public/private key PEM file, without a password.

Path is relative to the container so you will need to mount a volume with your certificate e.g. /data/mycert.pem.

During start up, your certificate will be copied automatically to the ~/.vnc folder and arguments passed to websockify.

> [!WARNING]
> By default (without `--no-exit-on-failure` set) if your certificate expires during the session, the server will auto terminate due to failing health checks. This _currently_ happens without warning.

### --no-exit-on-failure
Specifies whether the health check should **NOT** explode the docker container if the desktop becomes unhealthy. Generally you want to leave the default behavour alone as it allows the container to clean itself up if you specify the `--rm` flag or to restart itself if you specify the `--restart=always` flag. However if you want to be able to recover the desktop/files in the event of a crash you may wish to set this.

## Application Support
Whaletop supports a basic form of application mapping whereby any `.desktop` files present in the `/Apps` folder will be automatically copied to the `/usr/share/applications` directory before the X server is started (thereby avoiding the need to restart the UI panels to pickup the changes).

Generally it is recommended if you are going to mount applications for the user you do it on a subfolder basis rather than `/Apps` as the `/Apps` folder is the recommended way of customising the container to include applications and mounting it will explode any customisations present.

> [!WARNING]
> When mounting application folders, especially if they are going to be shared between multiple users, it is **strongly** recommended that you mount them read only to avoid users from being able to edit the applications.

Also note that there is no smarts to auto-remap paths in your .desktop files, so you will need to ensure they have the correct full path based on how you are planning to mount them.

When the `/Apps` folder is present, the start up script recursively searches through the folder to an infinite depth so you can safely nest your files several layers down to avoid squashing any container level customisations. 

An example invocation for an appimage is as follows:
```
docker run -it --rm -p 8080:8080 -v "`pwd`"/Apps/SomeApp:/Apps/SomeApp:ro --security-opt seccomp=$(pwd)/chrome.json mbainrot/whaletop
```

## Chromium Sandboxing
So in order for Chromium based applications (such as many AppImages, Google Chrome, Chromium browser, Firefox etc) to function with sandboxing enabled, they need to be able to access certain system operations.

There are two supported methods that Whaletop supports to address this

### Docker Security Option - Sec Comp Policy
This is the recommended way as it abides by the principal of least priviledge. To do this add the following docker commandline option to your `docker run` command

```
docker run -it --rm --security-opt seccomp=$(pwd)/chrome.json -p 8080:8082 mbainrot/whaletop
```

This method is based on the fantastic work by Jessie Frazelle.

### Priviledged Mode
This way is not so recommended as it results in excessive system permissions such as SYS_ADMIN to be granted to the docker container, which could result in a container escape.

To do this add `--priviledged` to the docker commandline

```
docker run -it --rm --priviledged -p 8080:8082 mbainrot/whaletop
```

### No-sandbox mode
This way is also not recommended and should not be performed unless you trust the sites that the chromium component will be accessing. Additionally it will usually cause applications to complain about no sandboxing as it is considered unsafe.

In general this can be done by appending --no-sandbox to app-images but it is dependant on the application and sometimes does not work.

## AppImages & Containers
There is a limitation if we want to stay within best practices guidelines as inorder to be able to fuse we need to not only enable riskier privileges such as SYS_ADMIN but we also need to expose the /dev/fuse device which is generally considered insecure.

This container has the environment variable APPIMAGE_EXTRACT_AND_RUN=1 baked in to work around this but in the event of it not working you can append `--appimage-extract-and-run` to your AppImage's commandline.

# Credits:
* Jessie Frazelle for the docker sec policy chrome.json - https://blog.jessfraz.com/post/how-to-use-new-docker-seccomp-profiles/
* nuntius-dev/KDEPlasmaDesktopinDocker for their wonderful docker file to which this container is based off. Their one file dockerfile really simplified how the magic works with docker based desktops.
* https://github.com/AppImage/AppImageKit/wiki/FUSE for the instructions on how to work around the FUSE issue with docker.