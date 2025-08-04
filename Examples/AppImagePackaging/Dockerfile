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