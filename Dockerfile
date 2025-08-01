FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    DISPLAY=:1 \
    APPIMAGE_EXTRACT_AND_RUN=1 \
    VNC_PORT=5901 \
    NOVNC_PORT=8080

# Update and install required dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    locales locales-all \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    xfonts-base x11-xserver-utils \
    wget curl nano sudo \
    git unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install our desktop manager, bang in --no-install-recommends so
# to avoid picking up unwanted ""optional"" garbage 
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    task-lxde-desktop \
    desktop-file-utils \
    menu \
    lxtask \
    lxlauncher \
    xdg-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install apt based apps
RUN apt-get update && \
    apt-get install -y libnss3 chromium && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install start script dependancies
RUN apt-get update && \
    apt-get install -y python3-psutil python3-openssl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Generate locales
RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

# FIXME: Need to workout a better fix for this, as lxpolkit is somewhat useful
# Kill off lxpolkit
RUN rm /etc/xdg/autostart/lxpolkit.desktop && mv /usr/bin/lxpolkit /usr/bin/lxpolkit.dead || true

# Symlink vnc.html in noVnc to make our life easierrrr
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Remove tigervncconfig from /etc/X11/Xtigervnc-session to stop the "VNC Config" window from showing up
RUN sed 's/tigervncconfig -iconic &//' /etc/X11/Xtigervnc-session > /etc/X11/Xtigervnc-session.new && \
cp /etc/X11/Xtigervnc-session.new /etc/X11/Xtigervnc-session

# Create state folders so if orchestrated the orchestrator knows whether the container is healthy, the vnc password (if random), etc, etc
RUN mkdir -p /opt/whaletop

# Add our run script
ADD Scripts/start.py /start.py
RUN chmod +x /start.py

# Expose ports for VNC and noVNC
EXPOSE 5901 8080

# Command to start the container
CMD ["/start.py"]