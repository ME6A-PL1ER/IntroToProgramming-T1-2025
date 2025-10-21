"""
Educational Memory Editor - A simplified version of Cheat Engine
This tool demonstrates how memory scanning and editing works.

EDUCATIONAL PURPOSE ONLY - Shows basic concepts of:
- Memory scanning
- Value searching
- Memory modification
- Process enumeration and attachment
"""

import ctypes
import struct
import sys
import time
import psutil
from ctypes import wintypes

# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

class MemoryEditor:
    """Educational memory editor for scanning and modifying values"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.process_handle = None
        self.pid = None
        self.process_name = None
        self.found_addresses = []
        self.value_type = 'int32'  # Default value type
        
    def open_process(self, pid):
        """Open a process for reading/writing"""
        self.pid = pid
        try:
            process = psutil.Process(pid)
            self.process_name = process.name()
        except:
            self.process_name = "Unknown"
            
        self.process_handle = self.kernel32.OpenProcess(
            PROCESS_ALL_ACCESS, False, pid
        )
        if not self.process_handle:
            raise Exception(f"Failed to open process {pid}. May need administrator privileges.")
        return True
    
    def close_process(self):
        """Close the process handle"""
        if self.process_handle:
            self.kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
    
    def read_memory(self, address, size):
        """Read memory from a specific address"""
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        
        success = self.kernel32.ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )
        
        if success and bytes_read.value == size:
            return buffer.raw
        return None
    
    def write_memory(self, address, data):
        """Write data to a specific memory address"""
        size = len(data)
        bytes_written = ctypes.c_size_t()
        
        success = self.kernel32.WriteProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            data,
            size,
            ctypes.byref(bytes_written)
        )
        
        return success and bytes_written.value == size
    
    def scan_memory(self, value, value_type='int32', progress_callback=None):
        """
        Scan memory for a specific value
        value_type: 'int32', 'int64', 'float', 'double', 'byte'
        progress_callback: optional function to report progress
        """
        self.found_addresses = []
        self.value_type = value_type
        
        # Convert value to bytes
        if value_type == 'int32':
            search_bytes = struct.pack('<i', value)
            size = 4
        elif value_type == 'int64':
            search_bytes = struct.pack('<q', value)
            size = 8
        elif value_type == 'float':
            search_bytes = struct.pack('<f', value)
            size = 4
        elif value_type == 'double':
            search_bytes = struct.pack('<d', value)
            size = 8
        elif value_type == 'byte':
            search_bytes = bytes([value & 0xFF])
            size = 1
        else:
            raise ValueError(f"Unsupported value type: {value_type}")
        
        # Scan memory regions
        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        total_scanned = 0
        
        print(f"Scanning for {value_type} value: {value}")
        print("This may take a moment...\n")
        
        while address < 0x7FFFFFFF0000:  # Max user-mode address on x64
            # Query memory region
            result = self.kernel32.VirtualQueryEx(
                self.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi)
            )
            
            if result == 0:
                break
            
            # Check if region is readable
            if (mbi.State == MEM_COMMIT and 
                mbi.Protect in [PAGE_READONLY, PAGE_READWRITE, 
                               PAGE_WRITECOPY, PAGE_EXECUTE_READ, 
                               PAGE_EXECUTE_READWRITE]):
                
                # Read the region (limit to 10MB chunks to avoid issues)
                region_size = min(mbi.RegionSize, 10 * 1024 * 1024)
                data = self.read_memory(mbi.BaseAddress, region_size)
                
                if data:
                    # Search for the value
                    offset = 0
                    while offset < len(data) - size:
                        if data[offset:offset+size] == search_bytes:
                            found_address = mbi.BaseAddress + offset
                            self.found_addresses.append(found_address)
                        offset += 1
                    
                    total_scanned += region_size
                    if progress_callback and total_scanned % (50 * 1024 * 1024) == 0:
                        progress_callback(total_scanned)
            
            address = mbi.BaseAddress + mbi.RegionSize
        
        print(f"Found {len(self.found_addresses)} addresses")
        return self.found_addresses
    
    def filter_addresses(self, value, value_type=None):
        """Filter previously found addresses by checking current value"""
        if not self.found_addresses:
            return []
        
        # Use stored value type if not specified
        if value_type is None:
            value_type = self.value_type
        
        # Convert value to bytes
        if value_type == 'int32':
            search_bytes = struct.pack('<i', value)
            size = 4
        elif value_type == 'int64':
            search_bytes = struct.pack('<q', value)
            size = 8
        elif value_type == 'float':
            search_bytes = struct.pack('<f', value)
            size = 4
        elif value_type == 'double':
            search_bytes = struct.pack('<d', value)
            size = 8
        elif value_type == 'byte':
            search_bytes = bytes([value & 0xFF])
            size = 1
        
        filtered = []
        for address in self.found_addresses:
            data = self.read_memory(address, size)
            if data and data == search_bytes:
                filtered.append(address)
        
        self.found_addresses = filtered
        print(f"Filtered to {len(self.found_addresses)} addresses")
        return self.found_addresses
    
    def modify_value(self, address, value, value_type=None):
        """Modify a value at a specific address"""
        if value_type is None:
            value_type = self.value_type
            
        if value_type == 'int32':
            data = struct.pack('<i', value)
        elif value_type == 'int64':
            data = struct.pack('<q', value)
        elif value_type == 'float':
            data = struct.pack('<f', value)
        elif value_type == 'double':
            data = struct.pack('<d', value)
        elif value_type == 'byte':
            data = bytes([value & 0xFF])
        else:
            raise ValueError(f"Unsupported value type: {value_type}")
        
        return self.write_memory(address, data)
    
    def read_value(self, address, value_type=None):
        """Read a value from a specific address"""
        if value_type is None:
            value_type = self.value_type
            
        if value_type == 'int32':
            size = 4
            fmt = '<i'
        elif value_type == 'int64':
            size = 8
            fmt = '<q'
        elif value_type == 'float':
            size = 4
            fmt = '<f'
        elif value_type == 'double':
            size = 8
            fmt = '<d'
        elif value_type == 'byte':
            size = 1
            fmt = 'B'
        
        data = self.read_memory(address, size)
        if data:
            return struct.unpack(fmt, data)[0]
        return None
    
    def freeze_value(self, address, value, value_type=None, duration=10):
        """
        Continuously write a value to an address (freeze it)
        This is a simple implementation for educational purposes
        """
        if value_type is None:
            value_type = self.value_type
        
        print(f"Freezing address 0x{address:016X} to value {value} for {duration} seconds...")
        print("Press Ctrl+C to stop")
        
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                self.modify_value(address, value, value_type)
                time.sleep(0.1)  # Update every 100ms
            print("Freeze completed!")
        except KeyboardInterrupt:
            print("\nFreeze stopped by user")


def list_processes():
    """List all running processes"""
    print("\n" + "=" * 80)
    print("RUNNING PROCESSES")
    print("=" * 80)
    print(f"{'PID':<10} {'Name':<30} {'Memory (MB)':<15}")
    print("-" * 80)
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            info = proc.info
            mem_mb = info['memory_info'].rss / (1024 * 1024)
            processes.append((info['pid'], info['name'], mem_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by name
    processes.sort(key=lambda x: x[1].lower())
    
    for pid, name, mem in processes:
        print(f"{pid:<10} {name:<30} {mem:>10.2f}")
    
    return processes


def search_processes(query):
    """Search for processes by name"""
    print(f"\nSearching for processes matching '{query}'...")
    
    matches = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            info = proc.info
            if query.lower() in info['name'].lower():
                mem_mb = info['memory_info'].rss / (1024 * 1024)
                matches.append((info['pid'], info['name'], mem_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if matches:
        print(f"\nFound {len(matches)} matching process(es):")
        print(f"{'PID':<10} {'Name':<30} {'Memory (MB)':<15}")
        print("-" * 60)
        for pid, name, mem in matches:
            print(f"{pid:<10} {name:<30} {mem:>10.2f}")
    else:
        print("No matching processes found!")
    
    return matches


def demo_game():
    """A simple game to demonstrate memory editing"""
    print("=" * 60)
    print("DEMO GAME - Memory Editor Target")
    print("=" * 60)
    print("\nThis is a simple game where you have health and coins.")
    print("Use the memory editor to find and modify these values!\n")
    
    health = 100
    coins = 50
    score = 0
    
    print(f"Process ID (PID): {ctypes.windll.kernel32.GetCurrentProcessId()}")
    print("\nStarting values:")
    print(f"  Health: {health}")
    print(f"  Coins: {coins}")
    print(f"  Score: {score}")
    
    print("\nCommands:")
    print("  1 - Take damage (-10 health)")
    print("  2 - Spend coins (-5 coins)")
    print("  3 - Gain score (+100 points)")
    print("  q - Quit")
    print("\nWatch the values change, then use the memory editor to modify them!")
    print("-" * 60)
    
    while True:
        print(f"\n[Health: {health} | Coins: {coins} | Score: {score}]")
        choice = input("Your choice: ").strip().lower()
        
        if choice == '1':
            health = max(0, health - 10)
            print(f"You took damage! Health: {health}")
        elif choice == '2':
            if coins >= 5:
                coins -= 5
                print(f"You spent coins! Coins: {coins}")
            else:
                print("Not enough coins!")
        elif choice == '3':
            score += 100
            print(f"Score increased! Score: {score}")
        elif choice == 'q':
            print("Exiting demo game...")
            break
        else:
            print("Invalid choice!")


def memory_editor_interface():
    """Interactive memory editor interface"""
    editor = MemoryEditor()
    
    print("=" * 80)
    print("EDUCATIONAL MEMORY EDITOR")
    print("=" * 80)
    print("\nThis tool demonstrates how memory scanners work.")
    print("Attach to ANY process and modify its memory values!")
    print("\nIMPORTANT: Run as Administrator for best results")
    print("=" * 80)
    
    while True:
        status = ""
        if editor.process_handle:
            status = f" [Attached to: {editor.process_name} (PID: {editor.pid})]"
        
        print(f"\n{'='*80}")
        print(f"Main Menu{status}")
        print("=" * 80)
        print("  1 - List all processes")
        print("  2 - Search for process by name")
        print("  3 - Attach to process (by PID)")
        print("  4 - Scan for value")
        print("  5 - Filter results (next scan)")
        print("  6 - Show found addresses (with current values)")
        print("  7 - Modify address")
        print("  8 - Read address")
        print("  9 - Freeze value (keep writing for duration)")
        print("  0 - Detach from process")
        print("  q - Quit")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == '1':
            list_processes()
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            query = input("Enter process name to search: ").strip()
            matches = search_processes(query)
            if matches:
                try:
                    pid_choice = input("\nEnter PID to attach (or press Enter to skip): ").strip()
                    if pid_choice:
                        pid = int(pid_choice)
                        if editor.open_process(pid):
                            print(f"Successfully attached to process {pid}")
                except Exception as e:
                    print(f"Error: {e}")
        
        elif choice == '3':
            try:
                pid = int(input("Enter Process ID (PID): "))
                if editor.open_process(pid):
                    print(f"Successfully attached to {editor.process_name} (PID: {pid})")
            except Exception as e:
                print(f"Error: {e}")
                print("Tip: Try running as Administrator if you get access denied errors")
        
        elif choice == '4':
            if not editor.process_handle:
                print("Error: No process attached!")
                continue
            
            try:
                print("\nValue types:")
                print("  1 - int32 (4 bytes, -2,147,483,648 to 2,147,483,647)")
                print("  2 - int64 (8 bytes, very large integers)")
                print("  3 - float (4 bytes, decimal numbers)")
                print("  4 - double (8 bytes, precise decimals)")
                print("  5 - byte (1 byte, 0 to 255)")
                
                vtype = input("Value type (1-5, default=1): ").strip() or "1"
                type_map = {'1': 'int32', '2': 'int64', '3': 'float', '4': 'double', '5': 'byte'}
                value_type = type_map.get(vtype, 'int32')
                
                if value_type in ['float', 'double']:
                    value = float(input("Enter value to search for: "))
                else:
                    value = int(input("Enter value to search for: "))
                
                print(f"\nScanning memory of {editor.process_name}...")
                addresses = editor.scan_memory(value, value_type)
                
                if len(addresses) > 0:
                    if len(addresses) <= 20:
                        print("\nFound addresses:")
                        for i, addr in enumerate(addresses):
                            current_val = editor.read_value(addr, value_type)
                            print(f"  [{i}] 0x{addr:016X} = {current_val}")
                    else:
                        print(f"\nToo many addresses found ({len(addresses)})")
                        print("Try changing the value and use 'Filter' (option 5)")
                else:
                    print("No addresses found!")
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '5':
            if not editor.process_handle:
                print("Error: No process attached!")
                continue
            
            if not editor.found_addresses:
                print("Error: No previous scan results!")
                continue
            
            try:
                if editor.value_type in ['float', 'double']:
                    value = float(input("Enter current value: "))
                else:
                    value = int(input("Enter current value: "))
                    
                addresses = editor.filter_addresses(value)
                
                if len(addresses) <= 20:
                    print("\nRemaining addresses:")
                    for i, addr in enumerate(addresses):
                        current_val = editor.read_value(addr)
                        print(f"  [{i}] 0x{addr:016X} = {current_val}")
                else:
                    print(f"\nStill too many addresses ({len(addresses)})")
                    print("Change the value again and filter again!")
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '6':
            if editor.found_addresses:
                print(f"\nFound {len(editor.found_addresses)} addresses (showing up to 50):")
                print(f"{'Index':<8} {'Address':<20} {'Current Value':<15}")
                print("-" * 50)
                
                for i, addr in enumerate(editor.found_addresses[:50]):
                    try:
                        current_val = editor.read_value(addr)
                        print(f"{i:<8} 0x{addr:016X}    {current_val}")
                    except:
                        print(f"{i:<8} 0x{addr:016X}    [Read Error]")
                
                if len(editor.found_addresses) > 50:
                    print(f"\n... and {len(editor.found_addresses) - 50} more")
            else:
                print("No addresses found yet!")
        
        elif choice == '7':
            if not editor.process_handle:
                print("Error: No process attached!")
                continue
            
            try:
                print("\nEnter address:")
                print("  - Type index number (if you have scan results)")
                print("  - Type hex address (e.g., 0x1234ABCD)")
                
                addr_input = input("Address: ").strip()
                
                # Check if it's an index
                if addr_input.isdigit() and editor.found_addresses:
                    index = int(addr_input)
                    if 0 <= index < len(editor.found_addresses):
                        address = editor.found_addresses[index]
                    else:
                        print("Invalid index!")
                        continue
                else:
                    address = int(addr_input, 16)
                
                # Show current value
                current = editor.read_value(address)
                print(f"Current value at 0x{address:016X}: {current}")
                
                if editor.value_type in ['float', 'double']:
                    value = float(input("Enter new value: "))
                else:
                    value = int(input("Enter new value: "))
                
                if editor.modify_value(address, value):
                    new_val = editor.read_value(address)
                    print(f"✓ Successfully modified! New value: {new_val}")
                else:
                    print("✗ Failed to modify address!")
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '8':
            if not editor.process_handle:
                print("Error: No process attached!")
                continue
            
            try:
                addr_input = input("Enter address (hex, e.g., 0x1234ABCD) or index: ").strip()
                
                if addr_input.isdigit() and editor.found_addresses:
                    index = int(addr_input)
                    if 0 <= index < len(editor.found_addresses):
                        address = editor.found_addresses[index]
                    else:
                        print("Invalid index!")
                        continue
                else:
                    address = int(addr_input, 16)
                
                value = editor.read_value(address)
                
                if value is not None:
                    print(f"Value at 0x{address:016X}: {value} ({editor.value_type})")
                else:
                    print("Failed to read address!")
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '9':
            if not editor.process_handle:
                print("Error: No process attached!")
                continue
            
            try:
                addr_input = input("Enter address (hex or index): ").strip()
                
                if addr_input.isdigit() and editor.found_addresses:
                    index = int(addr_input)
                    if 0 <= index < len(editor.found_addresses):
                        address = editor.found_addresses[index]
                    else:
                        print("Invalid index!")
                        continue
                else:
                    address = int(addr_input, 16)
                
                if editor.value_type in ['float', 'double']:
                    value = float(input("Enter value to freeze: "))
                else:
                    value = int(input("Enter value to freeze: "))
                    
                duration = int(input("Duration in seconds (default=10): ").strip() or "10")
                
                editor.freeze_value(address, value, duration=duration)
            except KeyboardInterrupt:
                print("\nFreeze cancelled")
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == '0':
            editor.close_process()
            print("Detached from process")
        
        elif choice == 'q':
            print("Exiting memory editor...")
            editor.close_process()
            break
        else:
            print("Invalid choice!")


def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("EDUCATIONAL MEMORY EDITOR SUITE")
    print("=" * 80)
    print("\nWhat would you like to do?")
    print("  1 - Run demo game (target for memory editing)")
    print("  2 - Run memory editor (attach to ANY process)")
    print("  3 - Quick tutorial")
    print("  q - Quit")
    
    choice = input("\nYour choice: ").strip().lower()
    
    if choice == '1':
        demo_game()
    elif choice == '2':
        memory_editor_interface()
    elif choice == '3':
        print("\n" + "=" * 80)
        print("QUICK TUTORIAL")
        print("=" * 80)
        print("""
How to use this educational memory editor:

METHOD 1: Using the Demo Game
==============================
1. OPEN TWO TERMINAL WINDOWS
   - Run the demo game in one terminal
   - Run the memory editor in another terminal

2. IN THE DEMO GAME WINDOW:
   - Note the Process ID (PID) displayed
   - Remember your starting values (Health, Coins, Score)

3. IN THE MEMORY EDITOR WINDOW:
   - Choose option 1 to attach to the demo game using its PID
   - Choose option 2 to scan for a value (e.g., 100 for health)
   
4. FILTER RESULTS:
   - If too many addresses are found, go back to the game
   - Change the value (e.g., take damage: health becomes 90)
   - In the editor, choose option 3 and enter the new value (90)
   - Repeat until you have 1-3 addresses
   
5. MODIFY THE VALUE:
   - Choose option 5 to modify an address
   - Enter the index number or hex address
   - Enter your desired value (e.g., 9999)
   - Check the game to see if the value changed!

METHOD 2: Attaching to Any Process (Advanced)
==============================================
1. RUN THE MEMORY EDITOR AS ADMINISTRATOR
   - Right-click PowerShell → "Run as Administrator"
   - Navigate to your project directory
   - Run: python Practice\MemoryEditor.py

2. FIND YOUR TARGET PROCESS:
   - Choose option 1 to list all processes
   - OR choose option 2 to search by name (e.g., "notepad", "game")
   
3. ATTACH TO THE PROCESS:
   - Note the PID of your target
   - Choose option 3 and enter the PID
   
4. SCAN AND MODIFY:
   - Use the same scan/filter/modify workflow as above
   - Works with games, applications, or any running program!

TIPS FOR SUCCESS:
=================
- Start with simple values (health, score, money)
- Use unique values when possible (e.g., 1234 instead of 100)
- Filter multiple times to narrow down results
- Look for values that change frequently
- Try different value types (int32, float, double)
- Use the "freeze" feature to lock values in place

VALUE TYPES EXPLAINED:
======================
- int32: Standard integers (-2 billion to +2 billion)
- int64: Large integers (for big numbers)
- float: Decimal numbers (e.g., 123.45)
- double: High-precision decimals
- byte: Single byte (0-255)

EDUCATIONAL CONCEPTS:
====================
- Memory addresses: Where data is stored in RAM
- Memory scanning: Finding values by searching through memory
- Value filtering: Narrowing down results by comparing changes
- Memory modification: Changing values at specific addresses
- Value freezing: Continuously writing to prevent changes

This demonstrates how tools like Cheat Engine work!

LEGAL & ETHICAL NOTE:
=====================
This tool is for EDUCATIONAL PURPOSES ONLY. Use it to learn
about memory management and how programs work. Do not use it
to cheat in online games or violate terms of service.
        """)
        input("\nPress Enter to continue...")
        main()
    elif choice == 'q':
        print("Goodbye!")
    else:
        print("Invalid choice!")
        main()


if __name__ == "__main__":
    if sys.platform != "win32":
        print("This tool is designed for Windows only!")
        sys.exit(1)
    
    main()
