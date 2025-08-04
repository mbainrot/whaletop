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