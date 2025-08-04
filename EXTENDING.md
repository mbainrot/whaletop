# Extending Whaletop
One of the reasons I built whaletop was to better support users developing their own docker based desktops.

I have designed the container to try and make this as easy as possible.

In the below example I show a very basic extension of the desktop

## "Hello World" Example
```Dockerfile
FROM mbainrot/whaletop

# For this example we'll install nmap as it's pretty small
# Also it's good to clear the apt cache when your done to keep your chunks small
RUN apt-get update && \
    apt-get install -y nmap && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Then you include the ""standard footer"" to preserve the normal functionality
# ... thou you only have to do this if you want to :)

# Expose ports for VNC and noVNC
EXPOSE 5901 8080

# Command to start the container
CMD ["/start.py"]
```

## Application packaging example
In this example we'll install VSCodium appimage onto a docker container, this is a little more involved as we need to create a desktop file too.

> [!IMPORTANT]
> Note for this example as we're picking on a chromium based application, you will need to remember to set the sec-policy or the demo will not work.

This also demonstrates the auto .desktop functionality, whereby the startup script recurses /Apps and automatically copies any found .desktop files to `/usr/share/applications` so you don't have to remember which path to use. 

```Dockerfile
FROM mbainrot/whaletop

# Firstly we want to create our app folder
RUN mkdir -p /Apps/VSCodium

# First up we want to retrieve the appimage and the icon
RUN wget https://github.com/VSCodium/vscodium/releases/download/1.101.24242/VSCodium-1.101.24242.glibc2.29-x86_64.AppImage -O /Apps/VSCodium/VSCodium.AppImage && chmod +x /Apps/VSCodium/VSCodium.AppImage
RUN wget https://raw.githubusercontent.com/VSCodium/vscodium/refs/heads/master/icons/stable/codium_clt.svg -O /Apps/VSCodium/CodiumIcon.svg

# Next we will want create our desktop entry
RUN echo '[Desktop Entry]\n\
Version=1.0\n\
Name=VS Codium\n\
Comment=Simple Text Editor\n\
GenericName=Text Editor\n\
Exec=/Apps/VSCodium/VSCodium.AppImage %U\n\
Icon=/Apps/VSCodium/CodiumIcon.svg\n\
Terminal=false\n\
StartupNotify=true\n\
Type=Application\n\
Categories=Utility;TextEditor;GTK;\n\
MimeType=text/plain;' > /Apps/VSCodium/vscodium.desktop

# Then you include the ""standard footer"" to preserve the normal functionality
# ... thou you only have to do this if you want to :)

# Expose ports for VNC and noVNC
EXPOSE 5901 8080

# Command to start the container
CMD ["/start.py"]
```
