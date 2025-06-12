import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Scrollbar
from functools import wraps
from time import time
import hashlib
import binascii
import shutil
from main_file import decrypt_ds2_sl2, encrypt_modified_files
import csv



hex_pattern1_Fixed = "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF" #inventory
souls_distance = -1080  # Distance from the found hex pattern to the souls value
possible_name_distances_for_name_tap= [-1132]  #  distances from the found hex pattern to the character name
hex_pattern_end= 'FF FF FF FF'
found_slots = []  # Store found slots for editing
current_slot_index = 0  # Track which slot is currently selected

window = tk.Tk()
window.title("Elden Ring NightReign Save Editor")

try:
    # Set Theme Path
    azure_path = os.path.join(os.path.dirname(__file__), "Resources/Azure", "azure.tcl")
    window.tk.call("source", azure_path)
    window.tk.call("set_theme", "dark")  # or "light" for light theme
except tk.TclError as e:
    messagebox.showwarning("Theme Warning", f"Azure theme could not be loaded: {str(e)}")
file_path_var = tk.StringVar()
current_name_var = tk.StringVar(value="N/A")
new_name_var = tk.StringVar()
import_path_var=tk.StringVar()
current_souls_var = tk.StringVar(value="N/A")
new_souls_var = tk.StringVar()
current_section_var = tk.IntVar(value=0)
loaded_file_data = None
item_label_var = tk.StringVar()
item_label_var.set("Item ID:")  # Initial label
effect1_label_var = tk.StringVar()
effect1_label_var.set("Effect 1 ID:")  # Initial label
effect2_label_var = tk.StringVar()  
effect2_label_var.set("Effect 2 ID:")  # Initial label
effect3_label_var = tk.StringVar()
effect3_label_var.set("Effect 3 ID:")  # Initial label
effect4_label_var = tk.StringVar()
effect4_label_var.set("Effect 4 ID:")  # Initial label
working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)
def locate_name(file_path, offset):
    with open(file_path, 'rb') as f:
        f.seek(offset)
        raw = f.read(32)  # Assuming names are 32 bytes max (16 UTF-16 characters)
        try:
            decoded = raw.split(b'\x00\x00')[0].decode('utf-16le')
        except UnicodeDecodeError:
            return raw  # fallback if decoding fails
        return decoded

def locate_name1(file_path, offset):
    try:
        with open(file_path, 'rb') as file:
            file.seek(offset)
            name_data = file.read(10)
            print(f"Character Name: {name_data}")
            return name_data
    except IOError as e:
        messagebox.showerror("Error", f"Failed to read file: {str(e)}")
        return ""
    
def locate_name2(file_path, offset):
    try:
        with open(file_path, 'rb') as file:
            file.seek(offset)
            name_data = file.read(6)
            print(f"Character Name: {name_data}")
            return name_data
    except IOError as e:
        messagebox.showerror("Error", f"Failed to read file: {str(e)}")
        return ""
def read_file_section(file_path, start_offset, end_offset):
    try:
        with open(file_path, 'rb') as file:
            file.seek(start_offset)
            section_data = file.read(end_offset - start_offset + 1)
        return section_data
    except IOError as e:
        messagebox.showerror("Error", f"Failed to read file section: {str(e)}")
        return None

def find_hex_offset(section_data, hex_pattern):
    try:
        pattern_bytes = bytes.fromhex(hex_pattern)
        if pattern_bytes in section_data:
            return section_data.index(pattern_bytes)
        return None
    except ValueError as e:
        messagebox.showerror("Error", f"Failed to find hex pattern: {str(e)}")
        return None

def calculate_relative_offset(section_start, offset):
    return section_start + offset

def find_value_at_offset(section_data, offset, byte_size=4):
    try:
        value_bytes = section_data[offset:offset+byte_size]
        if len(value_bytes) == byte_size:
            return int.from_bytes(value_bytes, 'little')
    except IndexError:
        pass
    return None


def find_character_name(section_data, offset, byte_size=32):
    try:
        value_bytes = section_data[offset:offset+byte_size]
        name_chars = []
        for i in range(0, len(value_bytes), 2):
            char_byte = value_bytes[i]
            if char_byte == 0:
                break
            if 32 <= char_byte <= 126:
                name_chars.append(chr(char_byte))
            else:
                name_chars.append('.')
        return ''.join(name_chars)
    except IndexError:
        return "N/A"

def clean_decrypted_output_folder():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_dir, "decrypted_output")

    if os.path.exists(output_folder):
        print(f"🧹 Cleaning existing folder: {output_folder}")
        shutil.rmtree(output_folder)  # Removes the entire folder and its contents

    os.makedirs(output_folder)  # Recreate it clean
    print(f"✅ Ready: {output_folder}")    
##PC Stuff
def merge_userdata_files(input_file):
    clean_decrypted_output_folder()
    unpacked_folder = decrypt_ds2_sl2(input_file)
    print('lol')

    if not os.path.isdir(unpacked_folder):
        print(f"❌ Folder not found: {unpacked_folder}")
        return

    userdata_files = sorted(glob.glob(os.path.join(unpacked_folder, "USERDATA_*")))

    if len(userdata_files) != 14:
        print(f"⚠️ Expected 14 USERDATA files, found {len(userdata_files)}")
        return

    output_file = os.path.join(unpacked_folder, "memory.sl2")
    sizes = []

    with open(output_file, 'wb') as outfile:
        for file_path in userdata_files:
            with open(file_path, 'rb') as f:
                data = f.read()
                outfile.write(data)
                sizes.append(len(data))
            print(f"✅ Merged: {os.path.basename(file_path)} ({len(data)} bytes)")

    # Save size metadata
    sizes_path = os.path.join(unpacked_folder, "userdata_sizes.json")
    with open(sizes_path, 'w') as f:
        json.dump(sizes, f)

    print(f"📏 Sizes saved to: {sizes_path}")
    print(f"\n📦 All files merged into: {output_file}")
    return unpacked_folder

    

def split_memory_sl2(output_dir='split_userdata'):
    input_file = file_path_var.get()
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    # Look for the size metadata
    sizes_path = os.path.join(os.path.dirname(input_file), "userdata_sizes.json")
    if not os.path.exists(sizes_path):
        print("❗ Could not find 'userdata_sizes.json'. Cannot split without original sizes.")
        return

    with open(sizes_path, 'r') as f:
        sizes = json.load(f)

    with open(input_file, 'rb') as infile:
        data = infile.read()

    total_size = len(data)
    print(f"📦 Total file size: {total_size} bytes")
    print(f"📏 Loaded sizes: {sizes}")

    os.makedirs(output_dir, exist_ok=True)

    offset = 0
    for i, size in enumerate(sizes):
        chunk = data[offset:offset + size]
        output_path = os.path.join(output_dir, f"USERDATA_{i:02d}")
        with open(output_path, 'wb') as f:
            f.write(chunk)
        print(f"✅ Wrote {output_path} ({len(chunk)} bytes)")
        offset += size

    output_sl2_file=filedialog.asksaveasfilename(defaultextension=".sl2", filetypes=[("SL2 files", "*.sl2")], title="Save SL2 as")

    encrypt_modified_files(output_sl2_file)
    print(f"\n✅ All sections extracted to: {output_dir}/")
    

import glob
def open_file():
    global loaded_file_data, SECTIONS
    file_path = filedialog.askopenfilename(filetypes=[("Save Files", "*")])
    
    if file_path:
        file_name = os.path.basename(file_path)
        file_path_var.set(file_path)
        file_name_label.config(text=f"File: {file_name}")
        
        # Define sections based on file name
        if file_name.lower() == "memory.dat":
            print('lol')
            SECTIONS = {
                1: {'start': 0x80, 'end': 0x10007F},
                2: {'start': 0x100080, 'end': 0x20007F},
                3: {'start': 0x200080, 'end': 0x30007F},
                4: {'start': 0x300080, 'end': 0x40007F},
                5: {'start': 0x400080, 'end': 0x50007F},
                6: {'start': 0x500080, 'end': 0x60007F},
                7: {'start': 0x600080, 'end': 0x70007F},
                8: {'start': 0x700080, 'end': 0x80007F},
                9: {'start': 0x800080, 'end': 0x90007F},
                10: {'start': 0x900080, 'end': 0xA0007F}
            }
            print(f"DEBUG: file_name = '{file_name}'")
            file_path_var.set(file_path)
        elif file_name == "NR0000.sl2": ## to be done, no decrypted file available
            print(f"DEBUG: file_name = '{file_name}'")
            print('no')

            unpacked_folder=merge_userdata_files(file_path)
            if unpacked_folder is None:
                print('no unpacked folder')
            file_path = os.path.join(unpacked_folder, "memory.sl2")
            print("Trying to read from:", file_path)
            if not os.path.exists(file_path):
            
   
                print("memory.sl2 not found at:", file_path)
                
            file_path_var.set(file_path)
            SECTIONS = {
                1: {'start': 0x00000004, 'end': 0x00100003},
                2: {'start': 0x00100024, 'end': 0x00200023},
                3: {'start': 0x00200044, 'end': 0x00300043},
                4: {'start': 0x00300064, 'end': 0x00400063},
                5: {'start': 0x00400084, 'end': 0x00500083},
                6: {'start': 0x005000A4, 'end': 0x006000A3},
                7: {'start': 0x006000C4, 'end': 0x007000C3},
                8: {'start': 0x007000E4, 'end': 0x008000E3},
                9: {'start': 0x00800104, 'end': 0x00900103},
                10:{'start': 0x00900124, 'end': 0x00A00123}
            }
        try:
            with open(file_path, 'rb') as file:
                loaded_file_data = bytearray(file.read())
            
            # Create a backup
            backup_path = f"{file_path}.bak1"
            with open(backup_path, 'wb') as backup_file:
                backup_file.write(loaded_file_data)
            
            messagebox.showinfo("Backup Created", f"Backup saved as {backup_path}")
            
            # Enable section buttons
            for btn in section_buttons:
                btn.config(state=tk.NORMAL)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file or create backup: {str(e)}")
            return
def calculate_offset2(offset1, distance):
    return offset1 + distance



found_slots = []  # Store found slots for editing
current_slot_index = 0  # Track which slot is currently selected
items_json = {}  # Load from your items JSON file
effects_json = {}  # Load from your effects JSON file

def load_json_data():
    global items_json, effects_json
    try:
        file_path = os.path.join(working_directory, "Resources/Json")
        with open(os.path.join(file_path, 'items.json'), 'r') as f:
            items_json = json.load(f)
        with open(os.path.join(file_path, 'effects.json'), 'r') as f:
            effects_json = json.load(f)
    except FileNotFoundError:
        print("JSON files not found. Manual editing only will be available.")
        items_json = {}
        effects_json = {}

def load_section(section_number):
    if not loaded_file_data:
        messagebox.showerror("Error", "Please open a file first")
        return

    current_section_var.set(section_number)
    section_info = SECTIONS[section_number]
    section_data = loaded_file_data[section_info['start']:section_info['end'] + 1]

    file_name = os.path.basename(file_path_var.get()).lower()
    
    # Determine offset based on file name
    if file_name == "memory.dat":
        base_offset = 0xA019DE
        if 1 <= section_number <= 10:
            offset = base_offset + (section_number - 1) * 0x278
        else:
            messagebox.showerror("Error", f"Invalid section number: {section_number}")
            return
    elif file_name == "memory.sl2":
        # Section 1 starts at 0xA01AA2, each section offset is 632 (0x278) bytes apart
        base_offset = 0xA01AA2
        if 1 <= section_number <= 10:
            offset = base_offset + (section_number - 1) * 0x278
        else:
            messagebox.showerror("Error", f"Invalid section number: {section_number}")
            return
    else:
        messagebox.showerror("Error", f"Unknown file type: {file_name}")
        return
    print(file_name)
    # Now call locate_name with the correct offset
    name_bytes = locate_name(file_path_var.get(), offset)

    # Do something with section_data and name_bytes...
    print(f"Loaded section {section_number} with name: {name_bytes}")
    

    # Try to find hex pattern in the section
    offset1 = find_hex_offset(section_data, name_bytes.hex())
    if offset1 is None:
        name_bytes =locate_name1(file_path_var.get(), offset)
        offset1 = find_hex_offset(section_data, name_bytes.hex())
        if offset1 is None:
            name_bytes =locate_name2(file_path_var.get(), offset)
            offset1 = find_hex_offset(section_data, name_bytes.hex())
        
    if offset1 is not None:
        # Display Souls value
        souls_offset = offset1 + 52
        current_souls = find_value_at_offset(section_data, souls_offset)
        current_souls_var.set(current_souls if current_souls is not None else "N/A")

        # Display character name
        for distance in possible_name_distances_for_name_tap:
            name_offset = offset1
            current_name = find_character_name(section_data, name_offset)
            if current_name and current_name != "N/A":
                current_name_var.set(current_name)
                break
        else:
            current_name_var.set("N/A")

    else:
        current_souls_var.set("N/A")
        current_name_var.set("N/A")

def write_value_at_offset(file_path, offset, value, byte_size=4):
    value_bytes = value.to_bytes(byte_size, 'little')
    with open(file_path, 'r+b') as file:
        file.seek(offset)
        file.write(value_bytes)

def update_souls_value():
    file_path = file_path_var.get()
    section_number = current_section_var.get()
    
    if not file_path or not new_souls_var.get() or section_number == 0:
        messagebox.showerror("Input Error", "Please open a file and select a section!")
        return
    
    try:
        new_souls_value = int(new_souls_var.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid decimal number for Souls.")
        return

    section_info = SECTIONS[section_number]
    section_data = loaded_file_data[section_info['start']:section_info['end']+1]
    file_name = os.path.basename(file_path_var.get()).lower()
    
    # Determine offset based on file name
    if file_name == "memory.dat":
        base_offset = 0xA019DE
        if 1 <= section_number <= 10:
            offset = base_offset + (section_number - 1) * 0x278
        else:
            messagebox.showerror("Error", f"Invalid section number: {section_number}")
            return
    elif file_name == "memory.sl2":
        # Section 1 starts at 0xA01AA2, each section offset is 632 (0x278) bytes apart
        base_offset = 0xA01AA2
        if 1 <= section_number <= 10:
            offset = base_offset + (section_number - 1) * 0x278
        else:
            messagebox.showerror("Error", f"Invalid section number: {section_number}")
            return
    else:
        messagebox.showerror("Error", f"Unknown file type: {file_name}")
        return
    print(file_name)
    # Now call locate_name with the correct offset
    name_bytes = locate_name(file_path_var.get(), offset)
    

    # Try to find hex pattern in the section
    offset1 = find_hex_offset(section_data, name_bytes.hex())
    if offset1 is None:
        name_bytes =locate_name1(file_path_var.get(), offset) # Adjust the offset as needed
        offset1 = find_hex_offset(section_data, name_bytes.hex())
        if offset1 is None:
            name_bytes =locate_name2(file_path_var.get(), offset)  # Adjust the offset as needed
            offset1 = find_hex_offset(section_data, name_bytes.hex())
    
    if offset1 is not None:
        souls_offset = offset1 + 52
        write_value_at_offset(file_path, section_info['start'] + souls_offset, new_souls_value)
        messagebox.showinfo("Success", f"Souls value updated to {new_souls_value}. Reload section to verify.")
    else:
        messagebox.showerror("Pattern Not Found", "Pattern not found in the selected section.")

## Fixed replacing logic
def empty_slot_finder_aow(file_path, pattern_offset_start, pattern_offset_end):
    global found_slots 
    
    def get_slot_size(b4):
        if b4 == 0xC0:
            return 72
        elif b4 == 0x90:
            return 16
        elif b4 == 0x80:
            return 80
        else:
            return None
    
    start_pos = pattern_offset_start
    end_pos = pattern_offset_end
    valid_b4_values = {0x80, 0x90, 0xC0}
    
    try:
        with open(file_path, 'rb') as file:
            file.seek(start_pos)
            section_data = file.read(end_pos - start_pos)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"[DEBUG] Loaded section of {len(section_data)} bytes from {start_pos} to {end_pos}")

    # Clear previous results
    found_slots.clear()

    # STEP 1: Find alignment point by scanning for valid slots
    def is_valid_slot_start(pos):
        """Check if position could be the start of a valid slot"""
        if pos + 4 > len(section_data):  # Need at least 4 bytes
            return False, None
        
        b3, b4 = section_data[pos+2], section_data[pos+3]
        if b3 in (0x80, 0x83) and b4 in valid_b4_values:
            slot_size = get_slot_size(b4)
            if slot_size and pos + slot_size <= len(section_data):
                return True, slot_size
        return False, None
    
    # Find the first valid slot
    start_offset = None
    for i in range(0, len(section_data) - 8):  # At least 8 bytes for empty slot check
        valid, first_slot_size = is_valid_slot_start(i)
        if valid:
            # Check if the next position after this slot also starts a valid slot
            next_pos = i + first_slot_size
            valid_next, _ = is_valid_slot_start(next_pos)
            
            # Or check if it's an empty slot (which is also valid)
            is_empty_next = (next_pos + 8 <= len(section_data) and 
                             section_data[next_pos:next_pos+8] == b'\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
            
            if valid_next or is_empty_next:
                start_offset = i
                print(f"[DEBUG] Found valid slot alignment at offset {i}")
                break
    
    if start_offset is None:
        print("[ERROR] No valid slot alignment found.")
        return

    # STEP 2: Process all slots from alignment with variable slot sizes
    valid_slot_count = 0
    i = start_offset

    while i < len(section_data) - 4:
        # Check if this is a valid slot
        if i + 4 <= len(section_data):
            b3, b4 = section_data[i+2], section_data[i+3]

            if b3 == 0x80 and b4 in valid_b4_values:
                slot_size = get_slot_size(b4)

                if slot_size and i + slot_size <= len(section_data):
                    valid_slot_count += 1

                    if b4 == 0xC0:
                        slot_data = section_data[i:i+slot_size]
                        
                        # Extract item ID (bytes 5-7 and 9-11, should be the same)
                        item_id_bytes = slot_data[4:7]  # 5th, 6th, 7th bytes (0-indexed)
                        item_id = int.from_bytes(item_id_bytes, byteorder='little')
                        
                        # Extract effect IDs
                        effect1_bytes = slot_data[16:20]  # 17th to 20th bytes (0-indexed)
                        effect2_bytes = slot_data[20:24]  # 21st to 24th bytes
                        effect3_bytes = slot_data[24:28]  # 25th to 28th bytes
                        effect4_bytes = slot_data[28:32]  # 29th to 32nd bytes
                    
                        
                        effect1_id = int.from_bytes(effect1_bytes, byteorder='little')
                        effect2_id = int.from_bytes(effect2_bytes, byteorder='little')
                        effect3_id = int.from_bytes(effect3_bytes, byteorder='little')
                        effect4_id = int.from_bytes(effect4_bytes, byteorder='little')
                        
                        slot_info = {
                            'offset': start_pos + i,  # Absolute offset in file
                            'size': slot_size,
                            'data': slot_data.hex(),
                            'raw_data': slot_data,
                            'item_id': item_id,
                            'effect1_id': effect1_id,
                            'effect2_id': effect2_id,
                            'effect3_id': effect3_id,
                            'effect4_id': effect4_id
                        }
                        found_slots.append(slot_info)
                        
                        print(f"[DEBUG] Found valid slot with b4=0xC0 at offset {i}, size {slot_size} bytes.")
                        print(f"Item ID: {item_id}, Effects: {effect1_id}, {effect2_id}, {effect3_id}. {effect4_id}")

                    i += slot_size
                    continue
        
        # Check for empty slots
        if i + 8 <= len(section_data) and section_data[i:i+8] == b'\x00\x00\x00\x00\xFF\xFF\xFF\xFF':
            print(f"[DEBUG] Found empty slot at offset {i}")
            i += 8  # Empty slots are typically 8 bytes
            continue
            
        # If we reach here, this position doesn't match any known pattern
        # Try the next byte position
        i += 1
    
    print(f"[DEBUG] Found {len(found_slots)} slots with b4=0xC0")
    
    # Update the replace tab with found slots
    update_replace_tab()

def find_hex_offsetss(section_data, hex_pattern):
    try:
        # Handle both bytes and hex string inputs
        if isinstance(hex_pattern, bytes):
            pattern_bytes = hex_pattern
        else:
            pattern_bytes = bytes.fromhex(hex_pattern)
            
        if pattern_bytes in section_data:
            return section_data.index(pattern_bytes)
        return None
    except ValueError as e:
        messagebox.showerror("Error", f"Failed to find hex pattern: {str(e)}")
        return None
def import_section():
    global loaded_file_data
    global current_stemaid_var
    messagebox.showinfo("Advice", "Make sure you have a readable name not dots (...) or anything that could occure multiple times in the file")
    if not loaded_file_data:
        messagebox.showerror("Error", "Please open a file first")
        return

    current_section = current_section_var.get()
    if not current_section:
        messagebox.showerror("Error", "Please Choose a slot first")
        return
    

    import_path = filedialog.askopenfilename(filetypes=[("Save Files", "*")])
    if not import_path:
        return

    import_file_name = os.path.basename(import_path)

    # Define import sections
    if import_file_name.lower() == "memory.dat":
        import_sections = {
            1: {'start': 0x80, 'end': 0x10007F},
            2: {'start': 0x100080, 'end': 0x20007F},
            3: {'start': 0x200080, 'end': 0x30007F},
            4: {'start': 0x300080, 'end': 0x40007F},
            5: {'start': 0x400080, 'end': 0x50007F},
            6: {'start': 0x500080, 'end': 0x60007F},
            7: {'start': 0x600080, 'end': 0x70007F},
            8: {'start': 0x700080, 'end': 0x80007F},
            9: {'start': 0x800080, 'end': 0x90007F},
            10: {'start': 0x900080, 'end': 0xA0007F}
        }
    elif import_file_name == "NR0000.sl2":
        print(f"DEBUG: file_name = '{import_file_name}'")
        print('no')

        unpacked_folder=merge_userdata_files(import_path)
        if unpacked_folder is None:
            print('no unpacked folder')
        import_path = os.path.join(unpacked_folder, "memory.sl2")
        print("Trying to read from:", import_path)
        if not os.path.exists(import_path):
        

            print("memory.sl2 not found at:", import_path)
            
        import_path_var.set(import_path)
        import_sections = {
                1: {'start': 0x00000004, 'end': 0x00100003},
                2: {'start': 0x00100024, 'end': 0x00200023},
                3: {'start': 0x00200044, 'end': 0x00300043},
                4: {'start': 0x00300064, 'end': 0x00400063},
                5: {'start': 0x00400084, 'end': 0x00500083},
                6: {'start': 0x005000A4, 'end': 0x006000A3},
                7: {'start': 0x006000C4, 'end': 0x007000C3},
                8: {'start': 0x007000E4, 'end': 0x008000E3},
                9: {'start': 0x00800104, 'end': 0x00900103},
                10:{'start': 0x00900124, 'end': 0x00A00123}
            }
    else:
        messagebox.showerror("Unsupported File", "Unsupported file format for import.")
        return

    try:
        with open(import_path, 'rb') as f:
            import_data = bytearray(f.read())
        # Find the Steam ID at offset 0xA00148 (8 bytes)
        steam_offset = 0xA00148
        if steam_offset + 8 <= len(import_data):
            steam_id_bytes = import_data[steam_offset:steam_offset+8]
            # Replace all occurrences of this 8-byte Steam ID with 8 zero bytes
            zero_bytes = b'\x00' * 8
            idx = 0
            while True:
                idx = import_data.find(steam_id_bytes, idx)
                if idx == -1:
                    break
                import_data[idx:idx+8] = zero_bytes
                idx += 8
        else:
            messagebox.showwarning("Warning", "Steam ID offset is out of range in the import file.")
         
    except Exception as e:
        messagebox.showerror("Error", f"Could not read import file: {e}")
        return
    # Extract names for all sections
    section_names = []
    # Calculate name_offsets: start at 0xA01AA2, increment by 0x278 (632) for 10 sections
    name_offsets = [0xA01AA2,0xA01D1A,0xA01F92,0xA0220A,0xA02482,0xA026FA,0xA02972,0xA02BEA,0xA02E62,0xA030DA]

    # Store name bytes for all offsets in a list
    name_bytes_list = []
    with open(import_path, 'rb') as f:
        for name_offset in name_offsets:
            name_bytes = locate_name(import_path, name_offset)
            name_bytes_list.append(name_bytes)

    # Now process each section
    for sec_num, sec_info in import_sections.items():
        data = import_data[sec_info['start']:sec_info['end']+1]
        name_found = "N/A"
        
        # Loop over name_bytes_list and check each one
        for name_bytes in name_bytes_list:
            offset1 = find_hex_offsetss(data, name_bytes)
            if offset1 is not None:
                for distance in possible_name_distances_for_name_tap:
                    name_offset = offset1
                    name = find_character_name(data, name_offset)
                    if name and name != "N/A":
                        name_found = name
                        break
                if name_found != "N/A":
                    break

        section_names.append((sec_num, name_found))



    # UI to choose section to import
    section_window = tk.Toplevel()
    section_window.title("Import Section")
    section_window.geometry("350x400")

    label = tk.Label(section_window, text="Choose a section to import from:")
    label.pack(pady=10)

    for sec_num, name in section_names:
        btn_text = f"Section {sec_num} - {name}"
        def make_callback(s=sec_num):
            def callback():
                global loaded_file_data

                # Extract the section chunk to import
                imported_chunk = import_data[import_sections[s]['start']:import_sections[s]['end']+1]

                # Replace the section in the loaded file data
                local_start = SECTIONS[current_section]['start']
                local_end = SECTIONS[current_section]['end']
                loaded_file_data = (
                    loaded_file_data[:local_start] +
                    imported_chunk +
                    loaded_file_data[local_end+1:]
                )

                # ✅ Try to extract character name from imported_chunk
                new_name = "N/A"
                for name_bytes in name_bytes_list:
                    offset1 = find_hex_offsetss(imported_chunk, name_bytes)
                    if offset1 is not None:
                        for distance in possible_name_distances_for_name_tap:
                            name_offset = offset1
                            name = find_character_name(imported_chunk, name_offset)
                            if name and name != "N/A":
                                new_name = name
                                break
                        if new_name != "N/A":
                            break

                # ✅ Replace all occurrences of the old name in loaded_file_data
                if new_name != "N/A":
                    try:
                        # Get name from the currently loaded section (before replacing it)
                        base_offset = 0xA019DE
                        section_number = current_section
                        if 1 <= section_number <= 10:
                            name_offset = base_offset + (section_number - 1) * 0x278
                            old_name = find_character_name(loaded_file_data, name_offset)
                        else:
                            old_name = "N/A"
                        if old_name != "N/A":
                            old_name_bytes = old_name.encode('utf-16le') + b'\x00\x00'
                            new_name_bytes = new_name.encode('utf-16le') + b'\x00\x00'

                            count = 0
                            idx = 0
                            while True:
                                idx = loaded_file_data.find(old_name_bytes, idx)
                                if idx == -1:
                                    break
                                loaded_file_data[idx:idx+len(old_name_bytes)] = new_name_bytes.ljust(len(old_name_bytes), b'\x00')
                                idx += len(old_name_bytes)
                                count += 1

                            print(f"✓ Replaced {count} occurrences of '{old_name}' with '{new_name}'")
                        else:
                            print("⚠ Could not detect old name for replacement.")
                    except Exception as e:
                        print(f"⚠ Failed to patch names: {e}")

                # Save to file
                with open(file_path_var.get(), 'wb') as f:
                    f.write(loaded_file_data)

                messagebox.showinfo("Import Successful", f"Replaced current section with Section {s} from import file.")
                load_section(current_section)
                section_window.destroy()
            return callback

        btn = tk.Button(section_window, text=btn_text, command=make_callback())
        btn.pack(pady=5)

###
def find_and_replace_pattern_with_aow_and_update_counters():
    global loaded_file_data
    try:
        # Get file path
        file_path = file_path_var.get()
        section_number = current_section_var.get()
        if not file_path or section_number == 0:
            messagebox.showerror("Error", "No file selected or section not chosen. Please load a file and select a section.")
            return

        # Get section information
        section_info = SECTIONS[section_number]
        
        # Convert loaded_file_data to bytearray if it's not already
        if isinstance(loaded_file_data, bytes):
            loaded_file_data = bytearray(loaded_file_data)
        
        # Get current section data from loaded_file_data
        section_data = loaded_file_data[section_info['start']:section_info['end']+1]
        file_name = os.path.basename(file_path_var.get()).lower()
    
        # Determine offset based on file name
        if file_name == "memory.dat":
            base_offset = 0xA019DE
            if 1 <= section_number <= 10:
                offset = base_offset + (section_number - 1) * 0x278
            else:
                messagebox.showerror("Error", f"Invalid section number: {section_number}")
                return
        elif file_name == "memory.sl2":
            # Section 1 starts at 0xA01AA2, each section offset is 632 (0x278) bytes apart
            base_offset = 0xA01AA2
            if 1 <= section_number <= 10:
                offset = base_offset + (section_number - 1) * 0x278
            else:
                messagebox.showerror("Error", f"Invalid section number: {section_number}")
                return
        else:
            messagebox.showerror("Error", f"Unknown file type: {file_name}")
            return
        print(file_name)
        # Now call locate_name with the correct offset
        name_bytes = locate_name(file_path_var.get(), offset)

        # Locate Fixed Pattern 1
        fixed_pattern_offset = find_hex_offset(section_data, name_bytes.hex())
        print(fixed_pattern_offset)
        
        if fixed_pattern_offset is None:
            fixed_pattern_offset=0xffff
            messagebox.showerror("Error", "Due to character name not being found, unrelated items could be shown.")
            
        fixed_pattern_offset_start = fixed_pattern_offset
        search_start_position = fixed_pattern_offset_start + len(hex_pattern1_Fixed) + 1000
        
        if search_start_position >= len(section_data):
            print("Search start position beyond section data.")
            return
            
        fixed_pattern_offset_end = find_hex_offset(section_data[search_start_position:], hex_pattern_end)
        if fixed_pattern_offset_end is not None:
            fixed_pattern_offset_end += search_start_position
        else:
            # Handle case where end pattern isn't found
            print("End pattern not found")
            return

        # Call the slot finder with corrected parameters
        empty_slot_finder_aow(file_path, section_info['start'] + 32, section_info['start'] + fixed_pattern_offset - 100)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to add or update item: {e}")

def update_replace_tab():
    global current_slot_index, item_label_var,effect1_label_var, effect2_label_var, effect3_label_var, effect4_label_var

    if not found_slots:
        slot_info_text.delete(1.0, tk.END)
        slot_info_text.insert(1.0, "No slots with b4=0xC0 found.")
        # Clear all entry fields
        item_id_entry.delete(0, tk.END)
        effect1_entry.delete(0, tk.END)
        effect2_entry.delete(0, tk.END)
        effect3_entry.delete(0, tk.END)
        effect4_entry.delete(0, tk.END)
        slot_navigation_label.config(text="No slots available")
        return

    # Reset to first slot if current index is out of bounds
    if current_slot_index >= len(found_slots):
        current_slot_index = 0

    # Display current slot info
    slot = found_slots[current_slot_index]

    # Extract IDs
    item_id = slot['item_id']
    effect1_id = slot['effect1_id']
    effect2_id = slot['effect2_id']
    effect3_id = slot['effect3_id']
    effect4_id = slot['effect4_id']

    # Look up names
    item_name = items_json.get(str(item_id), {}).get("name", "Unknown Item")
    effect1_name = effects_json.get(str(effect1_id), {}).get("name", "None")
    effect2_name = effects_json.get(str(effect2_id), {}).get("name", "None")
    effect3_name = effects_json.get(str(effect3_id), {}).get("name", "None")
    effect4_name = effects_json.get(str(effect4_id), {}).get("name", "None")
    item_label_var.set(f"Item ID:{item_id} - {item_name}")
    effect1_label_var.set(f"Effect 1 ID:{effect1_id} -{effect1_name}")
    effect2_label_var.set(f"Effect 2 ID:{effect2_id} -{effect2_name}" ) 
    effect3_label_var.set(f"Effect 3 ID:{effect3_id}- {effect3_name}")
    effect4_label_var.set(f"Effect 4 ID (Hidden slot):{effect4_id }-{effect4_name}")

    # Clear and insert info
    slot_info_text.delete(1.0, tk.END)
    slot_info_text.insert(1.0, f"Slot {current_slot_index + 1} of {len(found_slots)}\n")
    slot_info_text.insert(tk.END, f"Offset: {slot['offset']} (0x{slot['offset']:X})\n")
    slot_info_text.insert(tk.END, f"Size: {slot['size']} bytes\n")
    slot_info_text.insert(tk.END, f"Raw Data: {slot['data'][:32]}...\n\n")
    
    # Insert with names
    slot_info_text.insert(tk.END, f"Item ID: {item_id} - {item_name}\n")
    slot_info_text.insert(tk.END, f"Effect 1 ID: {effect1_id} - {effect1_name}\n")
    slot_info_text.insert(tk.END, f"Effect 2 ID: {effect2_id} - {effect2_name}\n")
    slot_info_text.insert(tk.END, f"Effect 3 ID: {effect3_id} - {effect3_name}\n")
    slot_info_text.insert(tk.END, f"Effect 4 ID: {effect4_id} - {effect4_name}\n")

    # Update entry fields
    item_id_entry.delete(0, tk.END)
    item_id_entry.insert(0, str(item_id))

    effect1_entry.delete(0, tk.END)
    effect1_entry.insert(0, str(effect1_id))

    effect2_entry.delete(0, tk.END)
    effect2_entry.insert(0, str(effect2_id))

    effect3_entry.delete(0, tk.END)
    effect3_entry.insert(0, str(effect3_id))

    effect4_entry.delete(0, tk.END)
    effect4_entry.insert(0, str(effect4_id))

    # Update navigation label
    slot_navigation_label.config(text=f"Slot {current_slot_index + 1} of {len(found_slots)}")


def navigate_slot(direction):
    global current_slot_index
    
    if not found_slots:
        return
    
    if direction == "prev":
        current_slot_index = (current_slot_index - 1) % len(found_slots)
    elif direction == "next":
        current_slot_index = (current_slot_index + 1) % len(found_slots)
    
    update_replace_tab()

def open_item_selector():
    if not items_json:
        messagebox.showwarning("Warning", "Items JSON not loaded. Please load items.json file.")
        return
    
    selector_window = tk.Toplevel(window)
    selector_window.title("Select Item")
    selector_window.geometry("400x500")
    
    # Create listbox with scrollbar
    frame = tk.Frame(selector_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    
    listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    listbox.pack(side="left", fill="both", expand=True)
    
    scrollbar.config(command=listbox.yview)
    
    # Populate listbox with items
    for item_id, item_data in items_json.items():
        item_name = item_data.get('name', f'Item {item_id}')
        listbox.insert(tk.END, f"{item_id}: {item_name}")
    
    def select_item():
        selection = listbox.curselection()
        if selection:
            item_text = listbox.get(selection[0])
            item_id = item_text.split(':')[0]
            item_id_entry.delete(0, tk.END)
            item_id_entry.insert(0, item_id)
            selector_window.destroy()
    
    tk.Button(selector_window, text="Select", command=select_item).pack(pady=10)

def open_effect_selector(effect_entry):
    if not effects_json:
        messagebox.showwarning("Warning", "Effects JSON not loaded. Please load effects.json file.")
        return
    
    selector_window = tk.Toplevel(window)
    selector_window.title("Select Effect")
    selector_window.geometry("400x500")
    
    # Create listbox with scrollbar
    frame = tk.Frame(selector_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    
    listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
    listbox.pack(side="left", fill="both", expand=True)
    
    scrollbar.config(command=listbox.yview)
    
    # Populate listbox with effects
    for effect_id, effect_data in effects_json.items():
        effect_name = effect_data.get('name', f'Effect {effect_id}')
        listbox.insert(tk.END, f"{effect_id}: {effect_name}")
    
    def select_effect():
        selection = listbox.curselection()
        if selection:
            effect_text = listbox.get(selection[0])
            effect_id = effect_text.split(':')[0]
            effect_entry.delete(0, tk.END)
            effect_entry.insert(0, effect_id)
            selector_window.destroy()
    
    tk.Button(selector_window, text="Select", command=select_effect).pack(pady=10)

def apply_slot_changes():
    global loaded_file_data, found_slots, current_slot_index
    
    if not found_slots or current_slot_index >= len(found_slots):
        messagebox.showerror("Error", "No slot selected for editing.")
        return
    
    try:
        # Get values from entry fields
        new_item_id = int(item_id_entry.get())
        new_effect1_id = int(effect1_entry.get())
        new_effect2_id = int(effect2_entry.get())
        new_effect3_id = int(effect3_entry.get())
        new_effect4_id = int(effect4_entry.get())
        
        current_slot = found_slots[current_slot_index]
        
        # Create a copy of the raw data to modify
        new_slot_data = bytearray(current_slot['raw_data'])
        
        # Update item ID in bytes 5-7 and 9-11 (0-indexed as 4-6 and 8-10)
        item_id_bytes = new_item_id.to_bytes(3, byteorder='little')
        new_slot_data[4:7] = item_id_bytes  # 5th, 6th, 7th bytes
        new_slot_data[8:11] = item_id_bytes  # 9th, 10th, 11th bytes (duplicate)
        
        # Update effect IDs
        effect1_bytes = new_effect1_id.to_bytes(4, byteorder='little')
        effect2_bytes = new_effect2_id.to_bytes(4, byteorder='little')
        effect3_bytes = new_effect3_id.to_bytes(4, byteorder='little')
        effect4_bytes = new_effect4_id.to_bytes(4, byteorder='little')
        
        new_slot_data[16:20] = effect1_bytes  # 17th to 20th bytes
        new_slot_data[20:24] = effect2_bytes  # 21st to 24th bytes
        new_slot_data[24:28] = effect3_bytes  # 25th to 28th bytes
        new_slot_data[28:32] = effect4_bytes  # 29th to 32nd bytes
        
        # Get file path
        file_path = file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "No file loaded.")
            return
        
        # Write changes to file
        with open(file_path, 'r+b') as file:
            file.seek(current_slot['offset'])
            file.write(new_slot_data)
        
        # Update loaded_file_data as well to keep it in sync
        start_idx = current_slot['offset']
        end_idx = start_idx + len(new_slot_data)
        loaded_file_data[start_idx:end_idx] = new_slot_data
        
        # Update the slot data in our tracking
        current_slot['data'] = new_slot_data.hex()
        current_slot['raw_data'] = new_slot_data
        current_slot['item_id'] = new_item_id
        current_slot['effect1_id'] = new_effect1_id
        current_slot['effect2_id'] = new_effect2_id
        current_slot['effect3_id'] = new_effect3_id
        current_slot['effect4_id'] = new_effect4_id
        
        # Refresh the display
        update_replace_tab()
        
        messagebox.showinfo("Success", f"Slot {current_slot_index + 1} updated successfully!")
        
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integer values for all IDs.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update slot: {e}")
def import_items_from_csv():

    if not found_slots:
        messagebox.showerror("Error", "No slots loaded. Scan for slots first.")
        return
    
    csv_file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV files", "*.csv")]
    )

    if not csv_file_path:
        return  # Cancelado

    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            
            for row in reader:
                try:
                    id = int(row['id']) - 1
                    if id < 0 or id >= len(found_slots):
                        print(f"Order {id + 1} is out of range. Skipping.")
                        continue
                    
                    slot = found_slots[id]
                    new_slot_data = bytearray(slot['raw_data'])
                    
                    # Item ID
                    item_id = int(row['item'])
                    item_id_bytes = item_id.to_bytes(3, byteorder='little')
                    new_slot_data[4:7] = item_id_bytes
                    new_slot_data[8:11] = item_id_bytes
                    
                    # Effects
                    for idx, eff_offset in enumerate(range(16, 28, 4)):
                        effect_col = f'effect{idx+1}'
                        effect_id = int(row.get(effect_col, 0))
                        effect_bytes = effect_id.to_bytes(4, byteorder='little')
                        new_slot_data[eff_offset:eff_offset+4] = effect_bytes
                    
                    # Write to file
                    with open(file_path_var.get(), 'r+b') as file:
                        file.seek(slot['offset'])
                        file.write(new_slot_data)
                    
                    # Update loaded data in memory
                    start_idx = slot['offset']
                    end_idx = start_idx + len(new_slot_data)
                    loaded_file_data[start_idx:end_idx] = new_slot_data

                    # Update slot info
                    slot['raw_data'] = new_slot_data
                    slot['data'] = new_slot_data.hex()
                    slot['item_id'] = item_id
                    for idx in range(5):
                        slot[f'effect{idx+1}_id'] = int(row.get(f'effect{idx+1}', 0))
                    
                    print(f"Updated slot {id + 1} successfully.")
                    
                except Exception as ex:
                    print(f"Error processing row {row}: {ex}")
        
        messagebox.showinfo("Import Complete", "CSV import completed successfully.")
        update_replace_tab()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to import CSV: {e}")
##UI stuff
file_open_frame = tk.Frame(window)
file_open_frame.pack(fill="x", padx=10, pady=5)

ttk.Button(file_open_frame, text="Open Save File", command=open_file).pack(side="left", padx=5)
file_name_label = tk.Label(file_open_frame, text="No file selected", anchor="w")
file_name_label.pack(side="left", padx=10, fill="x")

section_frame = tk.Frame(window)
section_frame.pack(fill="x", padx=10, pady=5)
section_buttons = []
for i in range(1, 11):
    btn = ttk.Button(section_frame, text=f"Slot {i}", command=lambda x=i: load_section(x), state=tk.DISABLED)
    btn.pack(side="left", padx=5)
    section_buttons.append(btn)

notebook = ttk.Notebook(window)
import_message_var = tk.StringVar()
import_message_label = ttk.Label(window, textvariable=import_message_var, foreground="green")
import_message_label.pack(pady=10)
import_btn = ttk.Button(window, text="Import Save(PC to PS4)", command=import_section)
import_btn.pack(pady=5)
# Change to ttk.Button for Azure theme
button_width = 15
ttk.Button(window, text="Save PC file", width=button_width, command=split_memory_sl2).pack(pady=10, padx=10)
# Change to ttk.Button for Azure theme


# Name tab
name_tab = ttk.Frame(notebook)
notebook.add(name_tab, text="Name")
ttk.Label(name_tab, text="Current Character Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
ttk.Label(name_tab, textvariable=current_name_var).grid(row=0, column=1, padx=10, pady=10)


souls_tab = ttk.Frame(notebook)
notebook.add(souls_tab, text="Murks/Runes")
ttk.Label(souls_tab, text="Current Souls:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
ttk.Label(souls_tab, textvariable=current_souls_var).grid(row=0, column=1, padx=10, pady=10)
ttk.Label(souls_tab, text="New Souls Value (MAX 999999999):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
ttk.Entry(souls_tab, textvariable=new_souls_var, width=20).grid(row=1, column=1, padx=10, pady=10)
ttk.Button(souls_tab, text="Update Souls", command=update_souls_value).grid(row=2, column=0, columnspan=2, pady=20)
# Replace tab
replace_tab = ttk.Frame(notebook)
notebook.add(replace_tab, text="Replace")

# === Scan Button ===
tk.Button(replace_tab, text="Scan for Relics", command=find_and_replace_pattern_with_aow_and_update_counters)\
    .grid(row=0, column=0, columnspan=4, pady=10)

# === Slot Info ===
ttk.Label(replace_tab, text="Slot Information:")\
    .grid(row=1, column=0, columnspan=4, padx=10, sticky="w")

slot_info_text = tk.Text(replace_tab, height=4, width=60, state=tk.NORMAL)
slot_info_text.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="ew")

# === Navigation Buttons ===
nav_frame = tk.Frame(replace_tab)
nav_frame.grid(row=3, column=0, columnspan=4, pady=10)

tk.Button(nav_frame, text="← Previous", command=lambda: navigate_slot("prev")).pack(side="left", padx=5)
slot_navigation_label = tk.Label(nav_frame, text="No slots available")
slot_navigation_label.pack(side="left", padx=20)
tk.Button(nav_frame, text="Next →", command=lambda: navigate_slot("next")).pack(side="left", padx=5)

# === Item ID Section ===
ttk.Label(replace_tab, textvariable=item_label_var)\
    .grid(row=4, column=0, padx=10, pady=(10, 2), sticky="w")

item_id_frame = tk.Frame(replace_tab)
item_id_frame.grid(row=5, column=0, padx=10, pady=2, sticky="ew")

item_id_entry = tk.Entry(item_id_frame, width=15)
item_id_entry.pack(side="left", padx=(0, 5))
tk.Button(item_id_frame, text="Select from JSON", command=open_item_selector).pack(side="left")

# === Effect 1 ===
ttk.Label(replace_tab, textvariable=effect1_label_var)\
    .grid(row=4, column=1, padx=10, pady=(10, 2), sticky="w")

effect1_frame = tk.Frame(replace_tab)
effect1_frame.grid(row=5, column=1, padx=10, pady=2, sticky="ew")

effect1_entry = tk.Entry(effect1_frame, width=15)
effect1_entry.pack(side="left", padx=(0, 5))
tk.Button(effect1_frame, text="Select from JSON", command=lambda: open_effect_selector(effect1_entry)).pack(side="left")

# === Effect 2 ===
ttk.Label(replace_tab, textvariable=effect2_label_var)\
    .grid(row=6, column=0, padx=10, pady=(10, 2), sticky="w")

effect2_frame = tk.Frame(replace_tab)
effect2_frame.grid(row=7, column=0, padx=10, pady=2, sticky="ew")

effect2_entry = tk.Entry(effect2_frame, width=15)
effect2_entry.pack(side="left", padx=(0, 5))
tk.Button(effect2_frame, text="Select from JSON", command=lambda: open_effect_selector(effect2_entry)).pack(side="left")

# === Effect 3 ===
ttk.Label(replace_tab, textvariable=effect3_label_var)\
    .grid(row=6, column=1, padx=10, pady=(10, 2), sticky="w")

effect3_frame = tk.Frame(replace_tab)
effect3_frame.grid(row=7, column=1, padx=10, pady=2, sticky="ew")

effect3_entry = tk.Entry(effect3_frame, width=15)
effect3_entry.pack(side="left", padx=(0, 5))
tk.Button(effect3_frame, text="Select from JSON", command=lambda: open_effect_selector(effect3_entry)).pack(side="left")

# === Effect 4 ===
ttk.Label(replace_tab, textvariable=effect4_label_var)\
    .grid(row=6, column=2, padx=10, pady=(10, 2), sticky="w")

effect4_frame = tk.Frame(replace_tab)
effect4_frame.grid(row=7, column=2, padx=10, pady=2, sticky="ew")

effect4_entry = tk.Entry(effect4_frame, width=15)
effect4_entry.pack(side="left", padx=(0, 5))
tk.Button(effect4_frame, text="Select from JSON", command=lambda: open_effect_selector(effect4_entry)).pack(side="left")

# === Apply Button ===
tk.Button(replace_tab, text="Apply Changes", command=apply_slot_changes, bg="orange", fg="white")\
    .grid(row=8, column=0, columnspan=4, padx=10, pady=20)

tk.Button(replace_tab, text="Import from CSV", command=import_items_from_csv, bg="green", fg="white").grid(row=8, column=1, columnspan=4, padx=10, pady=20)
# Configure column weights for resizing
replace_tab.columnconfigure(0, weight=1)
replace_tab.columnconfigure(1, weight=1)

notebook.pack(expand=1, fill="both")

# Load JSON data on startup
load_json_data()

my_label = tk.Label(window, text="Made by Alfazari911 --   Thanks to Nox and BawsDeep for help", anchor="e", padx=10)
my_label.pack(side="top", anchor="ne", padx=10, pady=5)

we_label = tk.Label(window, text="USE AT YOUR OWN RISK. EDITING STATS AND HP COULD GET YOU BANNED", anchor="w", padx=10)
we_label.pack(side="bottom", anchor="nw", padx=10, pady=5)

messagebox.showinfo("Info", "Contribute by adding the relics id's and effects's id to the json files at /src/Resources/Json in https://github.com/alfizari/Elden-Ring-Nightreign .")
# Run 
window.mainloop()
