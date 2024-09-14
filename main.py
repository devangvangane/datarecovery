import os
import tkinter as tk
import psutil
from tkinter import ttk
import threading
import hashlib

filetype_footer_header = {".png": [b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A", b"\x49\x45\x4E\x44\xAE\x42\x60\x82", "PNG"],
                          ".jpg": [b"\xff\xd8\xff\xe0\x00\x10\x4a\x46", b"\xff\xd9", "JPG"],
                          ".pdf": [b"%PDF-", b"%%EOF", "PDF"],
                          ".doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", None, "DOC"],
                          ".docx": [b"PK\x03\x04", None, "DOCX"],
                          ".ppt": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", None, "PPT"],
                          ".pptx": [b"\x50\x4B\03\x04", b"\x50\x4B\x05\x06", "PPTX"],
                          ".txt": [None, None, "TXT"]}


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
    return all(0x20 <= b <= 0x7E for b in byte_seq)
    # printable = set(bytes(string.printable, 'ascii'))  # ASCII encoded printable characters
    # return all(b in printable for b in byte_seq)


def recover_File():
    selected_drive = driveDropdown.get()
    selected_filetype = fileDropdown.get()
    file_header = None
    file_footer = None
    if selected_filetype != ".txt":
        file_header = filetype_footer_header[selected_filetype][0]
        file_footer = filetype_footer_header[selected_filetype][1]

    drive = f"\\\\.\\{selected_drive}"
    fileD = open(drive, "rb")
    if selected_filetype in [".pdf", ".txt"]:
        size = 16384
    else:
        size = 1024
    byte = fileD.read(size)
    offs = 0
    rcvd = 0

    directory = 'recFiles'
    if not os.path.exists(directory):
        os.makedirs(directory)

    while byte:
        if selected_filetype == ".txt" and is_printable(byte):
            print("entered if block")
            with open(os.path.join(directory, str(rcvd) + ".txt"), "wb") as fileN:
                print("Opened file")
                fileN.write(byte)
                while True:
                    byte = fileD.read(size)
                    print("read file")
                    if not byte or not is_printable(byte):
                        break
                    fileN.write(byte)
                    print("writing file")
            rcvd += 1
            continue

        if selected_filetype == ".ppt":
            found = byte.find(file_header)  # PPT header
            if found >= 0:
                # print(f"Found PPT header at offset: {found + offs * size}")
                with open(os.path.join(directory, f"ppt_file_{rcvd}.ppt"), "wb") as fileN:
                    fileN.write(byte[found:])
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

        if selected_filetype == ".doc":
            found = byte.find(file_header)
            if found >= 0:
                with open(os.path.join(directory, f"doc_file_{rcvd}.doc"), "wb") as fileN:
                    fileN.write(byte[found:])
                    while True:
                        byte = fileD.read(size)
                        if not byte:
                            break
                        fileN.write(byte)
                rcvd += 1
                continue

        if selected_filetype == ".docx":
            if byte.startswith(file_header):
                with open(os.path.join(directory, f"docx_file_{rcvd}.docx"), "wb") as fileN:
                    fileN.write(byte)
                    while True:
                        byte = fileD.read(size)
                        if not byte:
                            break
                        fileN.write(byte)
                rcvd += 1
                continue

        if selected_filetype not in [".txt", ".doc", ".docx", ".ppt"]:

            found = byte.find(file_header)  # PNG header
            # print(found)
            if found >= 0:
                drec = True
                # print(f'== Found {selected_filetype} at location: ' + str(hex(found + (size * offs))) + ' ==')

                fileN = open(os.path.join(directory, str(rcvd) + selected_filetype), "wb")
                fileN.write(byte[found:])
                while drec:
                    byte = fileD.read(size)
                    bfind = byte.find(file_footer)
                    if bfind >= 0:
                        fileN.write(byte[:bfind + len(file_footer)])
                        fileD.seek((offs + 1) * size)
                        # print(f'== Wrote {selected_filetype} to location: ' + os.path.join(directory, str(rcvd) + fileDropdown.get()) + ' ==\n')

                        drec = False
                        rcvd += 1
                        fileN.close()
                    else:
                        fileN.write(byte)
        byte = fileD.read(size)
        offs += 1

    fileD.close()


root = tk.Tk()
root.title("Data Recovery Application")
root.geometry("500x340")

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

fileTypes = [".png", ".jpg", ".pdf", ".doc", ".txt", ".docx", ".ppt", ".pptx"]
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

root.mainloop()

# coins - 2.47MB
# boats - 4.05MB
# pdf 37.9kb
