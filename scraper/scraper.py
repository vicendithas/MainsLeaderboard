import pokedex
import locations
import glob
import os
import time
import argparse

# Checks if the .SAV will open properly in PikaSAV.
def check_file_sav(file_path):
    start = 8201
    size = 2938
    checksum = 0
    
    # Read the file contents into a buffer
    with open(file_path, 'rb') as f:
        buffer = f.read()

    # Ensure the buffer has enough data
    if len(buffer) < start + size or len(buffer) < 11534 + 1:
        return False

    # Retrieve the stored checksum (bytes 11533 and 11534)
    stored_checksum = buffer[11533] + buffer[11534] * 256
    
    # Calculate the checksum for the specified range (from 8201 to 8201 + 2938 bytes)
    for x in range(size):
        checksum += buffer[x + start]
        checksum &= 65535  # Keep it within 16 bits

    # Check if the calculated checksum matches the stored one
    return checksum == stored_checksum    

def read_memory_address(file_path, address):
    with open(file_path, 'rb') as file:
        # Move the file pointer to the specified memory address
        file.seek(address)
        
        # Read the value at that address (1 byte for 8-bit integer)
        value_byte = file.read(1)  # Read 1 byte
        if len(value_byte) < 1:
            raise ValueError("Not enough data at the specified address.")
        
        # Convert the byte to a hexadecimal string
        hex_value = value_byte.hex()
        
        # Convert the hex value to decimal
        decimal_value = int(hex_value, 16)
        
        return hex_value, decimal_value

def get_creation_date(file_path):
    try:
        # Get the file creation time (Windows and some Unix systems)
        creation_time = os.path.getmtime(file_path)
    except AttributeError:
        # If the system doesn't support getctime, try the birthtime from os.stat()
        stat_info = os.stat(file_path)
        if hasattr(stat_info, 'st_birthtime'):
            creation_time = stat_info.st_birthtime
        else:
            # Fallback: Use last metadata change time if birthtime is unavailable
            creation_time = stat_info.st_mtime
    
    # Convert the timestamp to the 'm/dd/yyyy' format
    return time.strftime("%m/%d/%Y", time.localtime(creation_time))

def get_caught_level(file_path, address):
    hex_value, decimal_value = read_memory_address(file_path, address)
    
    # Extract the last 6 bits of the byte (mask with 0b00111111 or 63 in decimal)
    caught_level = decimal_value & 63
    
    return caught_level

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process .sav files and extract Pokémon data.")
    parser.add_argument("-l", "--level", action="store_true", help="Include Pokémon level in output")
    parser.add_argument("-n", "--name", action="store_true", help="Include filename in output")
    parser.add_argument("-f", "--format", action="store_true", help="Include format (Bingo or FIR) in output")
    parser.add_argument("-cl", "--caught-level", action="store_true", help="Include caught level in output")
    
    # Update addresses to include caught level addresses
    FIR_addresses = (0x00001A67, 0x00001A8C, 0x00001A8D, 0x0000288B)  # FIR caught level address
    Bingo_addresses = (0x00001A66, 0x00001A8B, 0x00001A8C, 0x0000288A)  # Bingo caught level address
    
    args = parser.parse_args()

    # Find all .sav files in the current working directory
    save_files = glob.glob("*.sav")
    sheet = ""  # Start with a blank sheet
    
    # Assume the SAV is FIR to start
    isBingo = False

    if not save_files:
        print("No .sav files found in the current directory.")
    else:
        for file_path in save_files:
            # Get the file creation date
            creation_date = get_creation_date(file_path)
            
            # Get rando format.
            isBingo = check_file_sav(file_path)
            
            # Read Pokemon information
            address = Bingo_addresses[0] if isBingo else FIR_addresses[0]
            hex_value, decimal_value = read_memory_address(file_path, address)
            pokemon = pokedex.pokedex.get(decimal_value)
            
            # Read Location information
            address = Bingo_addresses[1] if isBingo else FIR_addresses[1]
            hex_value, decimal_value = read_memory_address(file_path, address)
            location = locations.locations.get(decimal_value)
            
            # Prepare the entry without level, filename, or format
            ran_pokemon = f"{pokemon},{location},{creation_date}"
            
            # If the -l flag is provided, include the level
            if args.level:
                # Read Level information
                address = Bingo_addresses[2] if isBingo else FIR_addresses[2]
                hex_value, decimal_value = read_memory_address(file_path, address)
                level = decimal_value
                
                # Append level to the string
                ran_pokemon += f",{level}"
            
            # If the -n flag is provided, include the filename
            if args.name:
                # Append the filename to the string
                filename = os.path.basename(file_path)  # Get only the file name
                ran_pokemon += f",{filename}"
            
            # If the -f flag is provided, include the format
            if args.format:
                format_type = "Bingo" if isBingo else "FIR"
                ran_pokemon += f",{format_type}"

            # If the -cl flag is provided, include the caught level
            if args.caught_level:
                address = Bingo_addresses[3] if isBingo else FIR_addresses[3]  # Use the new caught level address
                caught_level = get_caught_level(file_path, address)
                ran_pokemon += f",{caught_level}"
            
            # Add a newline and append to the sheet
            ran_pokemon += "\n"
            sheet += ran_pokemon
        
        # Write the sheet to sav_history.csv
        with open("sav_history.csv", "w") as csv_file:
            csv_file.write(sheet)

        print("Data has been written to sav_history.csv")

