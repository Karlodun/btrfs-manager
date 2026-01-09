#!/usr/bin/env python3
"""
Btrfs Management Web Tool
A Flask-based web interface for managing Btrfs filesystems and Snapper snapshots
"""

import os
import subprocess
import json
import psutil
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime

app = Flask(__name__)

# HTML Template for the main page
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Btrfs Management Web Tool</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .btn { padding: 5px 10px; margin: 2px; cursor: pointer; }
        .success { color: green; }
        .error { color: red; }
        .warning { color: orange; }
        .stats-section { margin-bottom: 30px; }
        .section-title { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Btrfs Management Web Tool</h1>
        
        <div class="stats-section">
            <div class="section-title">System Information</div>
            <table id="sys-info-table">
                <thead>
                    <tr><th>Property</th><th>Value</th></tr>
                </thead>
                <tbody>
                    <tr><td>Hostname</td><td id="hostname"></td></tr>
                    <tr><td>Uptime</td><td id="uptime"></td></tr>
                    <tr><td>Load Average</td><td id="loadavg"></td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="section-title">Btrfs Filesystems <button class="btn" onclick="refreshBtrfs()">Refresh</button></div>
            <table id="btrfs-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Label</th>
                        <th>UUID</th>
                        <th>Devices</th>
                        <th>Total Size</th>
                        <th>Used</th>
                        <th>Free</th>
                        <th>Status</th>
                        <th>Mount Point</th>
                        <th>Mount Options</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="btrfs-body">
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="section-title">Block Devices <button class="btn" onclick="refreshDevices()">Refresh</button></div>
            <table id="devices-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Size</th>
                        <th>Type</th>
                        <th>Mount Point</th>
                        <th>FSType</th>
                        <th>Model</th>
                        <th>Serial</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="devices-body">
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="section-title">Btrfs RAID Status <button class="btn" onclick="refreshRaid()">Refresh</button></div>
            <table id="raid-table">
                <thead>
                    <tr>
                        <th>Filesystem</th>
                        <th>Data Profile</th>
                        <th>Metadata Profile</th>
                        <th>Global Reserve</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="raid-body">
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="section-title">Snapper Snapshots <button class="btn" onclick="refreshSnapshots()">Refresh</button></div>
            <table id="snapshots-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Pre Num</th>
                        <th>Description</th>
                        <th>Date</th>
                        <th>User</th>
                        <th>Used Space</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="snapshots-body">
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="section-title">I/O Statistics <button class="btn" onclick="refreshIo()">Refresh</button></div>
            <table id="io-table">
                <thead>
                    <tr>
                        <th>Device</th>
                        <th>Read Count</th>
                        <th>Write Count</th>
                        <th>Read Bytes</th>
                        <th>Write Bytes</th>
                        <th>Read Time (ms)</th>
                        <th>Write Time (ms)</th>
                    </tr>
                </thead>
                <tbody id="io-body">
                </tbody>
            </table>
        </div>
        
        <div class="stats-section">
            <div class="section-title">Actions</div>
            <button class="btn" onclick="addDevice()">Add Device to Btrfs</button>
            <button class="btn" onclick="createSnapshot()">Create Snapshot</button>
            <button class="btn" onclick="changeRaidLevel()">Change RAID Level</button>
        </div>
    </div>

    <script>
        // Initial load
        document.addEventListener('DOMContentLoaded', function() {
            refreshAll();
            setInterval(refreshAll, 30000); // Refresh every 30 seconds
        });
        
        function refreshAll() {
            refreshSysInfo();
            refreshBtrfs();
            refreshDevices();
            refreshRaid();
            refreshSnapshots();
            refreshIo();
        }
        
        function refreshSysInfo() {
            fetch('/api/sysinfo')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('hostname').textContent = data.hostname;
                    document.getElementById('uptime').textContent = data.uptime;
                    document.getElementById('loadavg').textContent = data.loadavg.join(', ');
                })
                .catch(error => console.error('Error fetching sys info:', error));
        }
        
        function refreshBtrfs() {
            fetch('/api/btrfs')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('btrfs-body');
                    tbody.innerHTML = '';
                    data.forEach(fs => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${fs.id}</td>
                            <td>${fs.label || '-'}</td>
                            <td>${fs.uuid}</td>
                            <td>${fs.devices.length}</td>
                            <td>${formatBytes(fs.total_size)}</td>
                            <td>${formatBytes(fs.used)}</td>
                            <td>${formatBytes(fs.free)}</td>
                            <td>${fs.status}</td>
                            <td>${fs.mount_point || '-'}</td>
                            <td>${fs.mount_options || '-'}</td>
                            <td>
                                <button class="btn" onclick="mountFs('${fs.uuid}')">Mount</button>
                                <button class="btn" onclick="umountFs('${fs.uuid}')">Unmount</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching btrfs info:', error));
        }
        
        function refreshDevices() {
            fetch('/api/devices')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('devices-body');
                    tbody.innerHTML = '';
                    data.forEach(dev => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${dev.name}</td>
                            <td>${formatBytes(dev.size)}</td>
                            <td>${dev.type}</td>
                            <td>${dev.mount_point || '-'}</td>
                            <td>${dev.fstype || '-'}</td>
                            <td>${dev.model || '-'}</td>
                            <td>${dev.serial || '-'}</td>
                            <td>
                                <button class="btn" onclick="addDeviceToBtrfs('${dev.name}')" ${dev.fstype === 'btrfs' ? '' : 'disabled'}>Add to Btrfs</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching device info:', error));
        }
        
        function refreshRaid() {
            fetch('/api/raid')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('raid-body');
                    tbody.innerHTML = '';
                    data.forEach(raid => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${raid.fs}</td>
                            <td>${raid.data_profile}</td>
                            <td>${raid.metadata_profile}</td>
                            <td>${formatBytes(raid.global_reserve)}</td>
                            <td>
                                <select id="raid-select-${raid.fs}">
                                    <option value="">Change RAID...</option>
                                    <option value="single">Single</option>
                                    <option value="raid0">RAID0</option>
                                    <option value="raid1">RAID1</option>
                                    <option value="raid5">RAID5</option>
                                    <option value="raid6">RAID6</option>
                                    <option value="raid10">RAID10</option>
                                </select>
                                <button class="btn" onclick="changeRaid('${raid.fs}', document.getElementById('raid-select-${raid.fs}').value)">Apply</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching RAID info:', error));
        }
        
        function refreshSnapshots() {
            fetch('/api/snapshots')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('snapshots-body');
                    tbody.innerHTML = '';
                    data.forEach(snap => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${snap.id}</td>
                            <td>${snap.type}</td>
                            <td>${snap.pre_num || '-'}</td>
                            <td>${snap.description}</td>
                            <td>${snap.date}</td>
                            <td>${snap.user_name}</td>
                            <td>${formatBytes(snap.used_space)}</td>
                            <td>
                                <button class="btn" onclick="deleteSnapshot('${snap.config}', ${snap.id})">Delete</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching snapshots:', error));
        }
        
        function refreshIo() {
            fetch('/api/io')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('io-body');
                    tbody.innerHTML = '';
                    data.forEach(io => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${io.device}</td>
                            <td>${io.read_count}</td>
                            <td>${io.write_count}</td>
                            <td>${formatBytes(io.read_bytes)}</td>
                            <td>${formatBytes(io.write_bytes)}</td>
                            <td>${io.read_time}</td>
                            <td>${io.write_time}</td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching IO stats:', error));
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function mountFs(uuid) {
            if (confirm(`Mount filesystem ${uuid}?`)) {
                fetch('/api/mount', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({uuid: uuid})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshBtrfs();
                })
                .catch(error => console.error('Error mounting filesystem:', error));
            }
        }
        
        function umountFs(uuid) {
            if (confirm(`Unmount filesystem ${uuid}?`)) {
                fetch('/api/umount', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({uuid: uuid})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshBtrfs();
                })
                .catch(error => console.error('Error unmounting filesystem:', error));
            }
        }
        
        function addDeviceToBtrfs(deviceName) {
            if (confirm(`Add device ${deviceName} to a Btrfs filesystem?`)) {
                const fsUuid = prompt("Enter the UUID of the Btrfs filesystem:");
                if (fsUuid) {
                    fetch('/api/add-device', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({device: deviceName, fs_uuid: fsUuid})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        refreshBtrfs();
                        refreshDevices();
                    })
                    .catch(error => console.error('Error adding device:', error));
                }
            }
        }
        
        function changeRaid(fs, newProfile) {
            if (newProfile && confirm(`Change RAID profile of ${fs} to ${newProfile}?`)) {
                fetch('/api/change-raid', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filesystem: fs, profile: newProfile})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshRaid();
                })
                .catch(error => console.error('Error changing RAID profile:', error));
            }
        }
        
        function deleteSnapshot(config, snapId) {
            if (confirm(`Delete snapshot ${snapId} from config ${config}?`)) {
                fetch('/api/delete-snapshot', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({config: config, id: snapId})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshSnapshots();
                })
                .catch(error => console.error('Error deleting snapshot:', error));
            }
        }
        
        function addDevice() {
            const devicePath = prompt("Enter the device path (e.g., /dev/sdb):");
            if (devicePath) {
                const label = prompt("Enter a label for the new Btrfs filesystem (optional):");
                fetch('/api/create-btrfs', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({device: devicePath, label: label})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshBtrfs();
                    refreshDevices();
                })
                .catch(error => console.error('Error creating Btrfs:', error));
            }
        }
        
        function createSnapshot() {
            const config = prompt("Enter the Snapper configuration name:");
            if (config) {
                const description = prompt("Enter a description for the snapshot:");
                if (description) {
                    fetch('/api/create-snapshot', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({config: config, description: description})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        refreshSnapshots();
                    })
                    .catch(error => console.error('Error creating snapshot:', error));
                }
            }
        }
        
        function changeRaidLevel() {
            // Implemented via the RAID table UI
            alert("Use the dropdown in the RAID table to change RAID levels.");
        }
    </script>
</body>
</html>
'''

def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def get_system_info():
    """Get basic system information"""
    hostname = run_command("hostname")
    
    # Get uptime
    uptime_raw = run_command("cat /proc/uptime")
    uptime_seconds = int(float(uptime_raw.split()[0]))
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime = f"{days}d {hours}h {minutes}m"
    
    # Get load average
    loadavg_raw = run_command("cat /proc/loadavg")
    loadavg = [float(x) for x in loadavg_raw.split()[:3]]
    
    return {
        "hostname": hostname,
        "uptime": uptime,
        "loadavg": loadavg
    }

def get_btrfs_filesystems():
    """Get information about Btrfs filesystems"""
    try:
        # List all btrfs filesystems
        cmd = "btrfs filesystem show"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return []
            
        output = result.stdout
        filesystems = []
        current_fs = None
        
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('Label:'):
                # Extract label, uuid, and other info from the line
                parts = line.split()
                if len(parts) >= 4:
                    label = parts[1].strip("'")
                    uuid = parts[3]
                    current_fs = {
                        'label': label,
                        'uuid': uuid,
                        'id': len(filesystems) + 1,
                        'devices': [],
                        'total_size': 0,
                        'used': 0,
                        'free': 0,
                        'status': 'active',
                        'mount_point': '',
                        'mount_options': ''
                    }
                    
                    # Find mount point
                    try:
                        mount_result = subprocess.run(f"findmnt -t btrfs -n -o TARGET,SOURCE | grep '{uuid}'", 
                                                     shell=True, capture_output=True, text=True)
                        if mount_result.returncode == 0:
                            mount_parts = mount_result.stdout.strip().split()
                            if mount_parts:
                                current_fs['mount_point'] = mount_parts[0]
                                
                                # Get mount options
                                opts_result = subprocess.run(f"findmnt -t btrfs -n -o OPTIONS,SOURCE | grep '{uuid}'", 
                                                             shell=True, capture_output=True, text=True)
                                if opts_result.returncode == 0:
                                    opts_parts = opts_result.stdout.strip().split()
                                    if opts_parts:
                                        current_fs['mount_options'] = opts_parts[0]
                    except:
                        pass
                        
            elif line.startswith('Total devices:') or line.startswith('devid') or line.startswith('Device location:'):
                # Parse device information
                if current_fs:
                    # Simple parsing - in a real implementation we'd parse more details
                    if 'devid' in line:
                        current_fs['devices'].append(line)
                        
            elif line.startswith('*** Some devices missing'):
                if current_fs:
                    current_fs['status'] = 'degraded'
                    
            elif line == '' and current_fs:
                # End of current filesystem info
                filesystems.append(current_fs)
                current_fs = None
                
        # If we still have a current filesystem at the end
        if current_fs:
            filesystems.append(current_fs)
            
        # Get size information for each filesystem
        for fs in filesystems:
            try:
                size_info = subprocess.run(f"btrfs filesystem usage -T {fs['mount_point'] or '/tmp'}", 
                                           shell=True, capture_output=True, text=True)
                if size_info.returncode == 0:
                    for sline in size_info.stdout.split('\n'):
                        if 'Data' in sline or 'Metadata' in sline or 'System' in sline:
                            # Parse size information
                            parts = sline.split()
                            if len(parts) >= 3 and 'Size:' in sline:
                                # Simplified parsing
                                break
            except:
                pass
                
        return filesystems
    except Exception as e:
        print(f"Error getting Btrfs filesystems: {e}")
        return []

def get_block_devices():
    """Get information about block devices"""
    try:
        cmd = "lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return []
            
        data = json.loads(result.stdout)
        devices = []
        
        def extract_devices(blockdevices, parent=""):
            for device in blockdevices:
                name = device.get('name', '')
                if parent:
                    name = f"{parent}{name}"
                
                dev_info = {
                    'name': name,
                    'size': parse_size(device.get('size', '0')),
                    'type': device.get('type', ''),
                    'mount_point': device.get('mountpoint', ''),
                    'fstype': device.get('fstype', ''),
                    'model': device.get('model', ''),
                    'serial': device.get('serial', '')
                }
                devices.append(dev_info)
                
                # Process children recursively
                if 'children' in device:
                    extract_devices(device['children'], f"{name}")
        
        if 'blockdevices' in data:
            extract_devices(data['blockdevices'])
            
        return devices
    except Exception as e:
        print(f"Error getting block devices: {e}")
        return []

def parse_size(size_str):
    """Convert size string to bytes"""
    if not size_str or size_str == '0':
        return 0
    
    units = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
    
    size_str = size_str.upper().strip()
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                num = float(size_str[:-1])
                return int(num * multiplier)
            except ValueError:
                return 0
    
    return 0

def get_raid_status():
    """Get RAID status for Btrfs filesystems"""
    try:
        cmd = "btrfs filesystem show"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return []
        
        raid_info = []
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'Label:' in line:
                # Extract filesystem info
                parts = line.split()
                if len(parts) >= 4:
                    uuid = parts[3]
                    raid_info.append({
                        'fs': uuid,
                        'data_profile': 'single',  # Default, would be parsed from actual output
                        'metadata_profile': 'single',
                        'global_reserve': 0
                    })
        
        # For now, return placeholder data until we implement proper parsing
        return [{
            'fs': 'main-filesystem',
            'data_profile': 'single',
            'metadata_profile': 'single', 
            'global_reserve': 0
        }]
    except Exception as e:
        print(f"Error getting RAID status: {e}")
        return []

def get_snapshots():
    """Get Snapper snapshots"""
    try:
        # First, list available configurations
        configs_output = run_command("snapper list-configs")
        configs = []
        
        lines = configs_output.split('\n')
        for line in lines[1:]:  # Skip header
            parts = line.strip().split()
            if parts:
                configs.append(parts[0])
        
        snapshots = []
        for config in configs:
            try:
                snaps_output = run_command(f"snapper -c {config} list")
                snap_lines = snaps_output.split('\n')[1:]  # Skip header
                
                for snap_line in snap_lines:
                    parts = snap_line.strip().split('|')
                    if len(parts) >= 6:
                        id_part = parts[0].strip()
                        type_part = parts[1].strip()
                        pre_num = parts[2].strip() if parts[2].strip() != '-' else None
                        description = parts[5].strip() if len(parts) > 5 else ''
                        
                        # Extract date
                        date_part = parts[3].strip() if len(parts) > 3 else ''
                        user_part = parts[4].strip() if len(parts) > 4 else ''
                        
                        snapshots.append({
                            'id': id_part,
                            'type': type_part,
                            'pre_num': pre_num,
                            'description': description,
                            'date': date_part,
                            'user_name': user_part,
                            'used_space': 0,  # Would need additional command to get this
                            'config': config
                        })
            except:
                continue  # Skip if config has issues
                
        return snapshots
    except Exception as e:
        print(f"Error getting snapshots: {e}")
        return []

def get_io_stats():
    """Get I/O statistics for devices"""
    try:
        io_stats = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                device_name = partition.device.split('/')[-1]  # Get base device name
                stats = psutil.disk_io_counters(perdisk=True)
                
                if device_name in stats:
                    stat = stats[device_name]
                    io_stats.append({
                        'device': device_name,
                        'read_count': stat.read_count,
                        'write_count': stat.write_count,
                        'read_bytes': stat.read_bytes,
                        'write_bytes': stat.write_bytes,
                        'read_time': stat.read_time,
                        'write_time': stat.write_time
                    })
            except:
                continue
                
        return io_stats
    except Exception as e:
        print(f"Error getting IO stats: {e}")
        return []

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/sysinfo')
def api_sysinfo():
    return jsonify(get_system_info())

@app.route('/api/btrfs')
def api_btrfs():
    return jsonify(get_btrfs_filesystems())

@app.route('/api/devices')
def api_devices():
    return jsonify(get_block_devices())

@app.route('/api/raid')
def api_raid():
    return jsonify(get_raid_status())

@app.route('/api/snapshots')
def api_snapshots():
    return jsonify(get_snapshots())

@app.route('/api/io')
def api_io():
    return jsonify(get_io_stats())

@app.route('/api/mount', methods=['POST'])
def api_mount():
    data = request.json
    uuid = data.get('uuid')
    
    # Find the device with this UUID
    try:
        result = subprocess.run(['blkid', '-U', uuid], capture_output=True, text=True)
        device_path = result.stdout.strip()
        
        if not device_path:
            return jsonify({'error': f'Device with UUID {uuid} not found'}), 404
            
        # Mount the device (assuming it's btrfs)
        # First create a temporary mount point or use a standard one
        mount_point = f'/mnt/btrfs_{uuid[:8]}'
        os.makedirs(mount_point, exist_ok=True)
        
        result = subprocess.run(['mount', device_path, mount_point], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({'message': f'Successfully mounted {device_path} to {mount_point}'})
        else:
            return jsonify({'error': f'Mount failed: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/umount', methods=['POST'])
def api_umount():
    data = request.json
    uuid = data.get('uuid')
    
    try:
        # Find the mount point for this UUID
        result = subprocess.run(['findmnt', '-t', 'btrfs', '-n', '-o', 'TARGET,SOURCE'], 
                                capture_output=True, text=True)
        
        mount_point = None
        for line in result.stdout.strip().split('\n'):
            if uuid in line:
                mount_point = line.split()[0]
                break
        
        if not mount_point:
            return jsonify({'error': f'No mounted filesystem found with UUID {uuid}'}), 404
            
        result = subprocess.run(['umount', mount_point], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({'message': f'Successfully unmounted {mount_point}'})
        else:
            return jsonify({'error': f'Unmount failed: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-device', methods=['POST'])
def api_add_device():
    data = request.json
    device = data.get('device')
    fs_uuid = data.get('fs_uuid')
    
    try:
        # Find the device path by UUID
        result = subprocess.run(['blkid', '-U', fs_uuid], capture_output=True, text=True)
        fs_device = result.stdout.strip()
        
        if not fs_device:
            return jsonify({'error': f'Filesystem with UUID {fs_uuid} not found'}), 404
            
        # Get the mount point for this filesystem
        result = subprocess.run(['findmnt', '-t', 'btrfs', '-n', '-o', 'TARGET,SOURCE'], 
                                capture_output=True, text=True)
        
        fs_mount_point = None
        for line in result.stdout.strip().split('\n'):
            if fs_uuid in line:
                fs_mount_point = line.split()[0]
                break
        
        if not fs_mount_point:
            return jsonify({'error': f'Filesystem with UUID {fs_uuid} is not mounted'}), 400
            
        # Add the device to the btrfs filesystem
        result = subprocess.run(['btrfs', 'device', 'add', device, fs_mount_point], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'message': f'Successfully added {device} to Btrfs filesystem'})
        else:
            return jsonify({'error': f'Adding device failed: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/change-raid', methods=['POST'])
def api_change_raid():
    data = request.json
    filesystem = data.get('filesystem')  # This should be the mount point
    profile = data.get('profile')
    
    try:
        # Convert profile to btrfs format (need to specify data and metadata profiles)
        valid_profiles = ['single', 'raid0', 'raid1', 'raid5', 'raid6', 'raid10']
        if profile not in valid_profiles:
            return jsonify({'error': f'Invalid RAID profile: {profile}'}), 400
        
        # Change the RAID profile
        result = subprocess.run(['btrfs', 'filesystem', 'resize', f'{profile}:', filesystem], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'message': f'Successfully changed RAID profile to {profile}'})
        else:
            # Try alternative command syntax
            result_alt = subprocess.run(['btrfs', 'balance', 'start', '-dconvert=' + profile, 
                                         '-mconvert=' + profile, filesystem], 
                                        capture_output=True, text=True)
            if result_alt.returncode == 0:
                return jsonify({'message': f'Successfully started RAID conversion to {profile}'})
            else:
                return jsonify({'error': f'RAID change failed: {result.stderr}\nAlternative: {result_alt.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-snapshot', methods=['POST'])
def api_delete_snapshot():
    data = request.json
    config = data.get('config')
    snap_id = data.get('id')
    
    try:
        result = subprocess.run(['snapper', '-c', config, 'delete', str(snap_id)], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'message': f'Successfully deleted snapshot {snap_id} from config {config}'})
        else:
            return jsonify({'error': f'Deletion failed: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-btrfs', methods=['POST'])
def api_create_btrfs():
    data = request.json
    device = data.get('device')
    label = data.get('label', '')
    
    try:
        cmd = ['mkfs.btrfs']
        if label:
            cmd.extend(['-L', label])
        cmd.append(device)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'message': f'Successfully created Btrfs filesystem on {device}'})
        else:
            return jsonify({'error': f'Creation failed: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-snapshot', methods=['POST'])
def api_create_snapshot():
    data = request.json
    config = data.get('config')
    description = data.get('description', 'Created via Web UI')
    
    try:
        result = subprocess.run(['snapper', '-c', config, 'create', '--description', description], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'message': f'Successfully created snapshot in config {config}'})
        else:
            return jsonify({'error': f'Creation failed: {result.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8787, debug=False)