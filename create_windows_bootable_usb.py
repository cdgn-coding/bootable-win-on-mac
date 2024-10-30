#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def check_root():
    if os.geteuid() != 0:
        print("Este script debe ser ejecutado con privilegios de superusuario (sudo).")
        sys.exit(1)

def unmount_usb(disk):
    try:
        subprocess.run(['diskutil', 'unmountDisk', disk], check=True)
        print(f"Desmontado {disk} exitosamente.")
    except subprocess.CalledProcessError:
        print(f"Error al desmontar {disk}. Asegúrate de que el dispositivo esté conectado.")
        sys.exit(1)

def erase_usb(disk, usb_name="WINUSB"):
    try:
        subprocess.run(['diskutil', 'eraseDisk', 'ExFAT', usb_name, 'GPT', disk], check=True)
        print(f"Formateado {disk} como ExFAT exitosamente.")
    except subprocess.CalledProcessError:
        print(f"Error al formatear {disk}.")
        sys.exit(1)

def mount_iso(iso_path):
    try:
        result = subprocess.run(['hdiutil', 'attach', iso_path, '-nobrowse', '-quiet'], check=True, stdout=subprocess.PIPE, text=True)
        mount_output = result.stdout
        for line in mount_output.splitlines():
            if '/Volumes/' in line:
                return line.split('\t')[-1]
        print("No se pudo montar el ISO.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("Error al montar el ISO.")
        sys.exit(1)

def copy_files(mount_point, usb_path):
    usb_mount_point = f"/Volumes/WINUSB"
    if not os.path.exists(usb_mount_point):
        subprocess.run(['diskutil', 'mount', usb_path], check=True)
    
    for root, dirs, files in os.walk(mount_point):
        relative_path = os.path.relpath(root, mount_point)
        target_dir = os.path.join(usb_mount_point, relative_path)
        os.makedirs(target_dir, exist_ok=True)
        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_dir, file)
            try:
                if os.path.getsize(source_file) > 4 * 1024 * 1024 * 1024:
                    # Archivo mayor a 4GB, particionar usando wimlib
                    subprocess.run(['wimlib-imagex', 'split', source_file, target_file, '4000'], check=True)
                    print(f"Archivo grande particionado: {file}")
                else:
                    shutil.copy2(source_file, target_file)
                    print(f"Copiado: {file}")
            except Exception as e:
                print(f"Error al copiar {file}: {e}")

def eject_usb(disk):
    try:
        subprocess.run(['diskutil', 'eject', disk], check=True)
        print(f"Expulsado {disk} exitosamente.")
    except subprocess.CalledProcessError:
        print(f"Error al expulsar {disk}.")

def main():
    if len(sys.argv) != 3:
        print("Uso: sudo python3 create_windows_bootable_usb.py /dev/diskX /path/to/windows.iso")
        sys.exit(1)
    
    usb_disk = sys.argv[1]
    iso_path = sys.argv[2]

    if not os.path.exists(iso_path):
        print(f"El archivo ISO no existe: {iso_path}")
        sys.exit(1)

    check_root()
    unmount_usb(usb_disk)
    erase_usb(usb_disk)
    mount_point = mount_iso(iso_path)
    copy_files(mount_point, usb_disk)
    subprocess.run(['hdiutil', 'detach', mount_point], check=True)
    eject_usb(usb_disk)
    print("USB booteable de Windows creado exitosamente.")

if __name__ == "__main__":
    main()
