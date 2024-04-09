#!/bin/bash

# Default UID and GID values with renamed variables
: ${UID:=1000}
: ${GID:=1000}

# Check if the UID/GID environment variables are set
if [ ! -z "$UID" ] && [ ! -z "$GID" ]; then
    # Create the group if it does not exist
    if ! getent group "$GID" ; then
        groupadd -g "$GID" pixivutil
    fi

    # Check if a user with the provided UID already exists
    # Using getent with the UID directly might not behave as expected, so we check against the user list
    if ! id -u "$UID" > /dev/null 2>&1; then
        # Create the user if it does not exist, using the updated UID and GID
        useradd -u "$UID" -g "$GID" -m -s /bin/bash pixivutil
    else
        # If the user already exists, ensure it's in the correct group
        # Find the username with the UID and apply usermod on it
        EXISTING_USER=$(getent passwd "$UID" | cut -d: -f1)
        usermod -g "$GID" "$EXISTING_USER"
    fi

    # Change ownership of the workdir and other necessary directories
    chown -R "$UID":"$GID" /workdir
fi

# Execute the Docker CMD
exec "$@"
