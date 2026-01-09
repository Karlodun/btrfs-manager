# Btrfs Management Web Tool

A comprehensive web-based tool for managing Btrfs filesystems and Snapper snapshots with a clean, intuitive interface.

## Features

- View all Btrfs filesystem stats (IDs, names, usage, mount points, mount options)
- Add/remove block devices or mark them for removal (degrade)
- View and change RAID levels
- Monitor current usage and I/O statistics
- Manage Snapper snapshots (create, delete, view)
- System information dashboard

## Requirements

- Python 3.6+
- Flask
- psutil
- btrfs-progs
- snapper

## Installation

Run the setup script:

```bash
sudo ./setup.sh
```

This will:
- Install required dependencies
- Set up the application in `/opt/btrfs-manager`
- Create a systemd service
- Start the service on port 8787

## Usage

Once installed, access the web interface at:
- `http://your-server-ip:8787`

The service runs with root privileges via systemd for full Btrfs management capabilities.

## Security Notice

This tool requires root privileges to manage Btrfs filesystems. Ensure appropriate network security measures are in place when exposing the service.

## Architecture

- Backend: Python Flask application
- Frontend: JavaScript/AJAX with responsive HTML/CSS
- Target directory: `/opt/btrfs-manager`
- Port: 8787
- Service: Managed by systemd