import os
import tkinter as tk
import psutil
from tkinter import ttk


filetype_footer_header = {".png": [b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A", b"\x49\x45\x4E\x44\xAE\x42\x60\x82", "PNG"],
                          ".jpg": [b"\xff\xd8\xff\xe0\x00\x10\x4a\x46", b"\xff\xd9", "JPG"],
                          ".pdf": ["hi", "PDF"],
                          ".doc": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "DOC"]}


def list_drives():
    partitions = psutil.disk_partitions()
    drives = []
    for partition in partitions:
        drive_letter = partition.device[0:2]
        drives.append(drive_letter)
    return drives


def recover_File():
    selected_drive = driveDropdown.get()
    selected_filetype = fileDropdown.get()
    file_header = filetype_footer_header[selected_filetype][0]
    file_footer = filetype_footer_header[selected_filetype][1]

    drive = f"\\\\.\\{selected_drive}"
    fileD = open(drive, "rb")
    size = 512
    byte = fileD.read(size)
    offs = 0
    rcvd = 0

    root.geometry("480x460")

    directory = 'recFiles'
    if not os.path.exists(directory):
        os.makedirs(directory)

    while byte:
        found = byte.find(file_header)  # PNG header
        if found >= 0:
            drec = True
            print(f'== Found {selected_filetype} at location: ' + str(hex(found + (size * offs))) + ' ==')

            text_area.insert(tk.END, f'== Found {selected_filetype} at location: ' + str(hex(found + (size * offs))) + ' ==')
            text_area.see(tk.END)

            fileN = open(os.path.join(directory, str(rcvd) + selected_filetype), "wb")
            fileN.write(byte[found:])
            while drec:
                byte = fileD.read(size)
                bfind = byte.find(file_footer)
                if bfind >= 0:
                    fileN.write(byte[:bfind + 2])
                    fileD.seek((offs + 1) * size)
                    print(f'== Wrote {selected_filetype} to location: ' + os.path.join(directory, str(rcvd) + fileDropdown.get()) + ' ==\n')

                    text_area.insert(tk.END, f'== Wrote {selected_filetype} to location: ' + os.path.join(directory, str(rcvd) + fileDropdown.get()) + ' ==\n')

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
root.geometry("480x460")

headLabel = tk.Label(root,
                     text="Data Recovery Application",
                     font=("Arial", 25, "bold"),
                     pady=10)
headLabel.pack()

driveOptions = list_drives()
driveDropdown = ttk.Combobox(root, values=driveOptions)
driveDropdown.set("Select Available Drive to Scan")
driveDropdown.place(x=20, y=70)
driveDropdown.config(width=30)
style = ttk.Style()
style.configure("TCombobox", padding=(20, 10, 20, 10), font=("Arial", 14))

driveDropdown.config(style="TCombobox")

fileTypes = [".png", ".jpg", ".pdf", ".doc", ".txt", ".docx"]
fileDropdown = ttk.Combobox(root, values=fileTypes)
fileDropdown.set("Select File Type")
fileDropdown.place(x=20, y=130)
fileDropdown.config(width=30)
fileDropdown.config(style="TCombobox")

text_area = tk.Text(root, height=10, width=40, font=("Arial", 14))
text_area.place(x=20, y=230)

recoverButton = tk.Button(root,
                          font=("Arial", 13, "bold"),
                          foreground="black",
                          background="#cfd1d1",
                          relief="flat",
                          cursor="hand2",
                          command=recover_File)
recoverButton.config(text=f"Recover files")
recoverButton.place(x=20, y=190)

root.mainloop()
