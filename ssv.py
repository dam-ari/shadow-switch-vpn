import os
import subprocess
import requests
from pathlib import Path

# Define URLs and paths
OPENVPN_INSTALLER_URL = {
    'windows': 'https://swupdate.openvpn.org/community/releases/openvpn-install-latest.exe',
    'mac': 'https://swupdate.openvpn.org/community/releases/openvpn-latest-stable.tar.gz',
    'linux': 'https://swupdate.openvpn.org/community/releases/openvpn-latest-stable.tar.gz'
}
VPNGATE_API_URL = 'https://www.vpngate.net/api/iphone/'
CONFIG_PATH = Path.home() / 'openvpn_configs'

def prompt_user(message):
    """Prompt the user for approval."""
    response = input(f"{message} (y/n): ").strip().lower()
    return response == 'y'

def is_openvpn_installed():
    """Check if OpenVPN is installed."""
    try:
        subprocess.run(["openvpn", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("OpenVPN is already installed.")
        return True
    except FileNotFoundError:
        print("OpenVPN is not installed.")
        return False

def install_openvpn(os_name):
    """Download and install OpenVPN based on the OS."""
    url = OPENVPN_INSTALLER_URL.get(os_name)
    if not url:
        print(f"No OpenVPN installer available for {os_name}.")
        return False

    # Prompt user for approval to download
    if not prompt_user(f"OpenVPN is not installed. Do you want to download the installer from {url}?"):
        print("Installation cancelled by user.")
        return False

    print(f"Downloading OpenVPN installer for {os_name}...")
    installer_path = Path.home() / f'openvpn_installer.{url.split(".")[-1]}'
    response = requests.get(url)
    with open(installer_path, 'wb') as f:
        f.write(response.content)

    print(f"Running OpenVPN installer for {os_name}...")
    if os_name == 'windows':
        subprocess.run([installer_path], check=True)
    elif os_name in ['linux', 'mac']:
        subprocess.run(["tar", "-xzf", installer_path, "-C", "/usr/local/bin"], check=True)
    
    print("OpenVPN installed successfully.")
    return True

def get_vpngate_config(location):
    """Fetch the OpenVPN configuration file from VPNGate."""
    response = requests.get(VPNGATE_API_URL)
    config_data = response.text

    # Find the desired location's config link
    config_lines = config_data.splitlines()
    for line in config_lines:
        if location.lower() in line.lower():
            parts = line.split(',')
            vpn_config_url = parts[-1]

            # Prompt user for approval to download
            if not prompt_user(f"Do you want to download the VPN configuration file for {location} from {vpn_config_url}?"):
                print("Download cancelled by user.")
                return None

            print(f"Downloading configuration for {location}...")
            config_response = requests.get(vpn_config_url)
            CONFIG_PATH.mkdir(parents=True, exist_ok=True)
            config_file_path = CONFIG_PATH / f"{location}.ovpn"
            with open(config_file_path, 'wb') as f:
                f.write(config_response.content)
            print(f"Configuration file saved to {config_file_path}.")
            return config_file_path

    print(f"Could not find a configuration file for {location}.")
    return None

def connect_vpn(config_path):
    """Connect to the VPN using the downloaded configuration file."""
    print(f"Connecting to VPN using {config_path}...")
    if os.name == 'nt':  # Windows
        subprocess.run(["openvpn", "--config", str(config_path)], check=True)
    else:  # macOS/Linux
        subprocess.run(["sudo", "openvpn", "--config", str(config_path)], check=True)
    print("Connected to the VPN.")

def main():
    os_name = os.name
    print("Starting VPN automation...")

    # Check if OpenVPN is installed
    if not is_openvpn_installed():
        if not install_openvpn(os_name):
            print("Failed to install OpenVPN.")
            return

    # Get user input for the desired location
    location = input("Enter the desired location (country) for the VPN: ")

    # Fetch the VPN configuration file
    config_path = get_vpngate_config(location)
    if not config_path:
        print("Failed to fetch the VPN configuration.")
        return

    # Connect to the VPN
    connect_vpn(config_path)

if __name__ == "__main__":
    main()
