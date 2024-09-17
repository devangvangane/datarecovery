import os
import tkinter as tk
import psutil
from tkinter import ttk
import threading
import hashlib
import time

filetype_footer_header = {".png": [b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A", b"\x49\x45\x4E\x44\xAE\x42\x60\x82", "PNG"],
                          ".jpg": [b"\xff\xd8\xff\xe0\x00\x10\x4a\x46", b"\xff\xd9", "JPG"],
                          ".pdf": [b"%PDF-", b"%%EOF", "PDF"],
                          ".doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", None, "DOC"],
                          ".docx": [b"PK\x03\x04", None, "DOCX"],
                          ".ppt": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", None, "PPT"],
                          ".pptx": [b"\x50\x4B\03\x04", b"\x50\x4B\x05\x06", "PPTX"],
                          ".xls": [b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1", None, "XLS"],  # No defined footer
                          ".xlsx": [b"\x50\x4B\x03\x04", b"\x50\x4B\x05\x06", "XLSX"],
                          ".gif": [[b"GIF87a", b"\x3B", "GIF"], [b"GIF89a", b"\x3B", "GIF"]],  # For GIF87a
                          ".exe": [b"\x4D\x5A", None, "EXE"],
                          ".txt": [None, None, "TXT"],
                          ".py": [None, None, "PY"],
                          ".rar": [b"\x52\x61\x72\x21\x1A\x07\x00", None, "RAR"],}


def start_recovery():
    # Create a new thread for the recover_File function
    recovery_thread = threading.Thread(target=recover_File)
    recovery_thread.start()


def calculate_hash(byte_data):
    hash_md5 = hashlib.md5()
    hash_md5.update(byte_data)
    return hash_md5.hexdigest()


def list_drives_windows():
    partitions = psutil.disk_partitions()
    drives = []
    for partition in partitions:
        drive_letter = partition.device[0:2]
        drives.append(drive_letter)
    return drives


def list_drives_linux():
    partitions = psutil.disk_partitions()
    drives = []
    for partition in partitions:
        if partition.device.startswith('/dev/'):
            drives.append(partition.device)
    return drives


def update_drives(event):
    selected_os = osystem.get()
    if selected_os == "Windows":
        driveOptions = list_drives_windows()
    else:
        driveOptions = list_drives_linux()

    driveDropdown['values'] = driveOptions
    driveDropdown.set("Select Available Drive to Scan")


def is_printable(byte_seq):
    printable_chars = set(range(0x20, 0x7E + 1))  # ASCII printable characters
    printable_chars.add(0x0A)  # newline (\n)
    printable_chars.add(0x0D)  # carriage return (\r)
    return all(b in printable_chars for b in byte_seq)


# def is_python_file(byte_seq):
#     # Decode bytes to string assuming UTF-8 encoding
#     try:
#         text = byte_seq.decode('utf-8')
#     except UnicodeDecodeError:
#         return False
#
#     # Simple checks for Python file structure
#     common_python_keywords = ["import", "def", "class", "from", "if", "while", "for", "print"]
#     for keyword in common_python_keywords:
#         if keyword in text:
#             return True
#
#     # Check for typical Python comment or encoding declaration
#     if text.startswith("#") or "# -*- coding:" in text:
#         return True
#
#     return False


def recover_File():
    selected_drive = driveDropdown.get()
    selected_filetype = fileDropdown.get()
    file_header = None
    file_footer = None
    if selected_filetype != ".txt" or selected_filetype != ".gif" or selected_filetype != ".py":
        file_header = filetype_footer_header[selected_filetype][0]
        file_footer = filetype_footer_header[selected_filetype][1]

    if selected_filetype == ".gif":
        file_header = [filetype_footer_header[".gif"][0][0], filetype_footer_header[".gif"][1][0]]
        file_footer = b"\x3B"

    if selected_filetype == ".py":
        file_header = None
        file_footer = None

    drive = f"\\\\.\\{selected_drive}"
    fileD = open(drive, "rb")

    total_size = os.path.getsize(drive) if os.path.exists(drive) else 10000000  # Fallback to estimate size
    size = 1024 if selected_filetype not in [".pdf", ".txt"] else 16384
    total_blocks = total_size // size

    progress_var.set(0)
    progress_bar["maximum"] = total_blocks

    byte = fileD.read(size)
    offs = 0
    rcvd = 0

    directory = 'recFiles'
    if not os.path.exists(directory):
        os.makedirs(directory)

    recovered_hashes = set()

    while byte:
        if selected_filetype == ".py":
            keywords = [b"import", b"def", b"class", b"# -*- coding: utf-8 -*-"]  # Common Python file keywords
            found = False
            for keyword in keywords:
                if byte.find(keyword) >= 0:
                    found = True
                    break
            if found:
                file_hash = calculate_hash(byte)
                if file_hash not in recovered_hashes:
                    with open(os.path.join(directory, f'{int(time.time())}-python_file_{rcvd}.py'), "wb") as fileN:
                        try:
                            # Try to decode bytes only for .py files, but catch decoding errors
                            text = byte.decode('utf-8', errors='ignore')  # 'ignore' will skip non-UTF-8 bytes
                            fileN.write(text.encode('utf-8'))  # Write back as UTF-8 after decoding
                        except UnicodeDecodeError as e:
                            print(f"Decoding error: {e}")
                            # If there are issues decoding, you can either skip or handle as necessary
                        recovered_hashes.add(file_hash)
                        max_size = 2 * 1024 * 1024  # Set a 10 MB limit for .py files
                        written_size = 0
                        while True:
                            byte = fileD.read(size)
                            if not byte or written_size >= max_size:
                                break
                            fileN.write(byte)  # Write the rest as binary or handle decoding carefully
                            written_size += len(byte)
                    rcvd += 1

        # if selected_filetype == ".txt" and is_printable(byte):
        #     file_hash = calculate_hash(byte)
        #     if file_hash not in recovered_hashes:
        #         with open(os.path.join(directory, f'{int(time.time())}_txt_file_' + str(rcvd) + ".txt"), "wb") as fileN:
        #             fileN.write(byte)
        #             recovered_hashes.add(file_hash)
        #             while True:
        #                 byte = fileD.read(size)
        #                 if not byte or not is_printable(byte):
        #                     break
        #                 fileN.write(byte)
        #         rcvd += 1
        #     byte = fileD.read(size)
        #     continue

        if selected_filetype == ".txt":
            text_block = b''
            print(f"Reading block {offs} for TXT recovery")
            # Collect printable byte sequences as long as the content looks like text
            while byte:
                if is_printable(byte):
                    text_block += byte
                    byte = fileD.read(size)
                else:
                    print(f"Non-printable byte sequence found at offset {offs}")
                    break

            if text_block:
                print(f"Recovered a text block of size {len(text_block)} bytes")

                # Try multiple encodings for decoding
                decoded_text = None
                for encoding in ['utf-8', 'iso-8859-1', 'ascii']:
                    try:
                        decoded_text = text_block.decode(encoding, errors='replace')  # Replace invalid characters
                        print(f"Decoded text block using {encoding} encoding.")
                        break
                    except (UnicodeDecodeError, LookupError):
                        print(f"Decoding with {encoding} failed. Trying next encoding.")

                if decoded_text is None:
                    decoded_text = text_block.decode('utf-8', errors='ignore')  # Ignore invalid characters
                    print(f"Using fallback decoding (ignoring invalid characters).")

                # Save the recovered text as a .txt file
                with open(os.path.join(directory, f"{rcvd}.txt"), "w", encoding='utf-8') as fileN:
                    fileN.write(decoded_text)
                rcvd += 1
            else:
                print("No valid text block found in this iteration.")
            byte = fileD.read(size)
            offs += 1
            continue

        if selected_filetype == ".rar":
            found = byte.find(file_header)
            if found >= 0:
                file_hash = calculate_hash(byte[found:])
                if file_hash not in recovered_hashes:
                    with open(os.path.join(directory, f"{int(time.time())}_rar_file_{rcvd}.rar"), "wb") as fileN:
                        fileN.write(byte[found:])
                        recovered_hashes.add(file_hash)

                        # Keep reading blocks until next file or EOF
                        while True:
                            byte = fileD.read(size)
                            if not byte:
                                break
                            next_header_pos = byte.find(file_header)
                            if next_header_pos >= 0:
                                fileN.write(byte[:next_header_pos])
                                break
                            else:
                                fileN.write(byte)
            rcvd += 1

        if selected_filetype == ".gif":
            for header in file_header:
                found = byte.find(header)
                if found >= 0:
                    file_hash = calculate_hash(byte[found:])
                    if file_hash not in recovered_hashes:
                        with open(os.path.join(directory,
                                               f"{int(time.time())}_{filetype_footer_header['.gif'][0][2]}_{rcvd}.gif"),
                                  "wb") as fileN:
                            fileN.write(byte[found:])
                            recovered_hashes.add(file_hash)
                            while True:
                                byte = fileD.read(size)
                                if not byte:
                                    break
                                footer_pos = byte.find(file_footer)
                                if footer_pos >= 0:
                                    fileN.write(byte[:footer_pos + 1])  # Include the footer byte
                                    break
                                else:
                                    fileN.write(byte)
                        rcvd += 1
                    break
            byte = fileD.read(size)
            offs += 1

        if selected_filetype == ".exe": # Still Issue
            # Search for EXE header
            found = byte.find(file_header)
            if found >= 0:
                file_hash = calculate_hash(byte[found:])
                if file_hash not in recovered_hashes:
                    # Start writing the EXE file once the header is found
                    with open(os.path.join(directory, f"{int(time.time())}_exe_file_{rcvd}.exe"), "wb") as fileN:
                        fileN.write(byte[found:])
                        recovered_hashes.add(file_hash)

                        total_written = len(byte[found:])

                        # Keep reading and writing until the next file header or EOF
                        while True:
                            byte = fileD.read(size)
                            if not byte:
                                break

                            # Check for the start of another file (e.g., another EXE or other headers)
                            next_header_pos = byte.find(file_header)
                            if next_header_pos >= 0:
                                fileN.write(byte[:next_header_pos])
                                break
                            else:
                                fileN.write(byte)
                            offs += 1
                            progress_var.set(offs)
                            root.update_idletasks()

                    rcvd += 1  # Increment recovered file count
            else:
                offs += 1  # No file header found, move forward

            # Read next block of data for the outer loop
            byte = fileD.read(size)

        if selected_filetype == ".ppt":
            found = byte.find(file_header)  # PPT header
            if found >= 0:
                file_hash = calculate_hash(byte[found:])
                if file_hash not in recovered_hashes:
                    with open(os.path.join(directory, f"{int(time.time())}_ppt_file_{rcvd}.ppt"), "wb") as fileN:
                        fileN.write(byte[found:])
                        recovered_hashes.add(file_hash)
                        while True:
                            byte = fileD.read(size)
                            if not byte:
                                break
                            # Continue reading until the end of the file
                            fileN.write(byte)
                    rcvd += 1
                byte = fileD.read(size)
                offs += 1
                continue

        if selected_filetype == ".doc" or selected_filetype == ".xls":
            found = byte.find(file_header)
            if found >= 0:
                file_hash = calculate_hash(byte[found:])
                if file_hash not in recovered_hashes:
                    with open(os.path.join(directory,
                                           f"{int(time.time())}-{filetype_footer_header[selected_filetype][2]}_file_{rcvd}{selected_filetype}"),
                              "wb") as fileN:
                        fileN.write(byte[found:])
                        recovered_hashes.add(file_hash)
                        while True:
                            byte = fileD.read(size)
                            if not byte:
                                break
                            fileN.write(byte)
                    rcvd += 1
                continue

        if selected_filetype == ".docx" or selected_filetype == ".xlsx":
            if byte.startswith(file_header):
                file_hash = calculate_hash(byte)
                if file_hash not in recovered_hashes:
                    with open(os.path.join(directory,
                                           f"{int(time.time())}-{filetype_footer_header[selected_filetype][2]}_file_{rcvd}{selected_filetype}"),
                              "wb") as fileN:
                        fileN.write(byte)
                        while True:
                            byte = fileD.read(size)
                            if not byte:
                                break
                            fileN.write(byte)
                    rcvd += 1
                continue

        if selected_filetype not in [".txt", ".doc", ".docx", ".ppt", ".exe", ".xlsx", ".xls", ".gif", ".py", ".rar"]:
            found = byte.find(file_header)
            if found >= 0:
                drec = True
                file_hash = calculate_hash(byte[found:])
                if file_hash not in recovered_hashes:
                    fileN = open(os.path.join(directory,
                                              f"{int(time.time())}-{filetype_footer_header[selected_filetype][2]}_file_" + str(
                                                  rcvd) + selected_filetype), "wb")
                    fileN.write(byte[found:])
                    while drec:
                        byte = fileD.read(size)
                        bfind = byte.find(file_footer)
                        if bfind >= 0:
                            fileN.write(byte[:bfind + len(file_footer)])
                            fileD.seek((offs + 1) * size)
                            drec = False
                            rcvd += 1
                            fileN.close()
                        else:
                            fileN.write(byte)
        byte = fileD.read(size)
        offs += 1

        progress_var.set(offs)
        root.update_idletasks()

    fileD.close()


root = tk.Tk()
root.title("Data Recovery Application")
root.geometry("500x400")

headLabel = tk.Label(root,
                     text="Data Recovery Application",
                     font=("Arial", 28, "bold"),
                     pady=10)
headLabel.pack()

style = ttk.Style()
style.configure("TCombobox", padding=(20, 10, 20, 10), font=("Arial", 14))

osOptions = ["Windows", "Linux"]
osystem = ttk.Combobox(root, values=osOptions)
osystem.set("Select Operating System")
osystem.place(x=30, y=70)
osystem.config(width=30)
osystem.config(style="TCombobox")
osystem.bind("<<ComboboxSelected>>", update_drives)

driveDropdown = ttk.Combobox(root)
driveDropdown.set("Select Available Drive to Scan")
driveDropdown.place(x=30, y=130)
driveDropdown.config(width=30)
driveDropdown.config(style="TCombobox")

fileTypes = [".png", ".jpg", ".pdf", ".doc", ".txt", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".gif", ".exe", ".py", ".rar"]
fileDropdown = ttk.Combobox(root, values=fileTypes)
fileDropdown.set("Select File Type")
fileDropdown.place(x=30, y=190)
fileDropdown.config(width=30)
fileDropdown.config(style="TCombobox")

recoverButton = tk.Button(root,
                          font=("Arial", 15, "bold"),
                          foreground="black",
                          background="#cfd1d1",
                          relief="flat",
                          cursor="hand2",
                          command=start_recovery)
recoverButton.config(text=f"Recover files")
recoverButton.place(x=40, y=250)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
progress_bar.place(x=30, y=320)

root.mainloop()