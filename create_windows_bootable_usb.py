#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

# Messages dictionary for easy internationalization
MESSAGES = {
    'es': {
        'root_required': "Este script debe ser ejecutado con privilegios de superusuario (sudo).",
        'unmount_success': "Desmontado {} exitosamente.",
        'unmount_error': "Error al desmontar {}. Asegúrate de que el dispositivo esté conectado.",
        'format_success': "Formateado {} como ExFAT exitosamente.",
        'format_error': "Error al formatear {}.",
        'iso_mount_error': "Error al montar el ISO.",
        'iso_mount_point_error': "No se pudo montar el ISO.",
        'large_file_split': "Archivo grande particionado: {}",
        'file_copied': "Copiado: {}",
        'copy_error': "Error al copiar {}: {}",
        'eject_success': "Expulsado {} exitosamente.",
        'eject_error': "Error al expulsar {}.",
        'iso_detach_success': "ISO desmontado exitosamente.",
        'iso_detach_error': "Error al desmontar el ISO.",
        'title': "\n=== Creación de USB booteable de Windows ===",
        'enter_iso': "\nIngrese la ruta al archivo ISO de Windows: ",
        'iso_not_found': "Error: El archivo ISO no existe. Por favor, verifique la ruta.",
        'available_disks': "\nDiscos disponibles:",
        'enter_disk': "\nIngrese el identificador del disco USB (ejemplo: /dev/diskX): ",
        'warning_format': "\n¡ADVERTENCIA! Se borrarán todos los datos en {}.\n¿Está seguro? (s/N): ",
        'disk_invalid': "Disco no válido o operación cancelada. Por favor, intente nuevamente.",
        'enter_name': "\nIngrese el nombre para el USB [{}]: ",
        'process_complete': "\nUSB booteable de Windows creado exitosamente.",
        'select_language': 'Seleccione el idioma / Select language:\n1. Español\n2. English\nOpción/Option [1]: ',
        'invalid_language': 'Opción inválida. Usando Español por defecto.'
    },
    'en': {
        'root_required': "This script must be run with superuser privileges (sudo).",
        'unmount_success': "{} unmounted successfully.",
        'unmount_error': "Error unmounting {}. Make sure the device is connected.",
        'format_success': "Formatted {} as ExFAT successfully.",
        'format_error': "Error formatting {}.",
        'iso_mount_error': "Error mounting ISO.",
        'iso_mount_point_error': "Could not mount ISO.",
        'large_file_split': "Large file split: {}",
        'file_copied': "Copied: {}",
        'copy_error': "Error copying {}: {}",
        'eject_success': "Ejected {} successfully.",
        'eject_error': "Error ejecting {}.",
        'iso_detach_success': "ISO detached successfully.",
        'iso_detach_error': "Error detaching ISO.",
        'title': "\n=== Windows Bootable USB Creation ===",
        'enter_iso': "\nEnter the path to Windows ISO file: ",
        'iso_not_found': "Error: ISO file does not exist. Please verify the path.",
        'available_disks': "\nAvailable disks:",
        'enter_disk': "\nEnter the USB disk identifier (example: /dev/diskX): ",
        'warning_format': "\nWARNING! All data on {} will be erased.\nAre you sure? (y/N): ",
        'disk_invalid': "Invalid disk or operation cancelled. Please try again.",
        'enter_name': "\nEnter name for the USB [{}]: ",
        'process_complete': "\nWindows bootable USB created successfully.",
        'select_language': 'Seleccione el idioma / Select language:\n1. Español\n2. English\nOpción/Option [1]: ',
        'invalid_language': 'Invalid option. Using English as default.'
    }
}

def get_message(key, lang='es', *args):
    """Get a message in the specified language with optional formatting"""
    message = MESSAGES[lang].get(key, f"Missing message: {key}")
    if args:
        return message.format(*args)
    return message

def check_root():
    if os.geteuid() != 0:
        print(get_message('root_required'))
        sys.exit(1)

def unmount_usb(disk):
    try:
        subprocess.run(['diskutil', 'unmountDisk', disk], check=True)
        print(get_message('unmount_success', 'es', disk))
    except subprocess.CalledProcessError:
        print(get_message('unmount_error', 'es', disk))
        sys.exit(1)

def erase_usb(disk, usb_name="WINUSB"):
    try:
        subprocess.run(['diskutil', 'eraseDisk', 'ExFAT', usb_name, 'GPT', disk], check=True)
        print(get_message('format_success', 'es', disk))
    except subprocess.CalledProcessError:
        print(get_message('format_error', 'es', disk))
        sys.exit(1)

def mount_iso(iso_path):
    try:
        result = subprocess.run(['hdiutil', 'attach', iso_path, '-nobrowse', '-quiet'], 
                              check=True, stdout=subprocess.PIPE, text=True)
        mount_output = result.stdout
        for line in mount_output.splitlines():
            if '/Volumes/' in line:
                return line.split('\t')[-1]
        print(get_message('iso_mount_point_error'))
        sys.exit(1)
    except subprocess.CalledProcessError:
        print(get_message('iso_mount_error'))
        sys.exit(1)

def copy_files(mount_point, usb_path, usb_name="WINUSB"):
    usb_mount_point = f"/Volumes/{usb_name}"
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
                    subprocess.run(['wimlib-imagex', 'split', source_file, target_file, '4000'], check=True)
                    print(get_message('large_file_split', 'es', file))
                else:
                    shutil.copy2(source_file, target_file)
                    print(get_message('file_copied', 'es', file))
            except Exception as e:
                print(get_message('copy_error', 'es', file, str(e)))

def eject_usb(disk):
    try:
        subprocess.run(['diskutil', 'eject', disk], check=True)
        print(get_message('eject_success', 'es', disk))
    except subprocess.CalledProcessError:
        print(get_message('eject_error', 'es', disk))

def list_available_disks():
    subprocess.run(['diskutil', 'list'], check=True)

def detach_iso(mount_point):
    try:
        subprocess.run(['hdiutil', 'detach', mount_point], check=True)
        print(get_message('iso_detach_success'))
    except subprocess.CalledProcessError:
        print(get_message('iso_detach_error'))
        sys.exit(1)

def select_language():
    """Prompt user to select language and return language code"""
    try:
        # We use Spanish for the initial prompt as it's the default
        choice = input(MESSAGES['es']['select_language']).strip()
        if not choice:  # Default to Spanish if empty
            return 'es'
        
        language_map = {
            '1': 'es',
            '2': 'en'
        }
        
        lang = language_map.get(choice, 'es')
        if choice not in language_map:
            print(MESSAGES[lang]['invalid_language'])
        
        return lang
    except Exception:
        return 'es'  # Default to Spanish if any error occurs

def get_absolute_path(path):
    """Convert relative path to absolute path"""
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.expanduser(path))

def get_user_inputs(lang):
    print(get_message('title', lang))
    
    # Get ISO path
    while True:
        iso_path = input(get_message('enter_iso', lang)).strip()
        # Convert to absolute path and expand user directory (~)
        iso_path = get_absolute_path(iso_path)
        if os.path.exists(iso_path):
            break
        print(get_message('iso_not_found', lang))
    
    # Get disk selection
    print(get_message('available_disks', lang))
    list_available_disks()
    while True:
        usb_disk = input(get_message('enter_disk', lang)).strip()
        if os.path.exists(usb_disk):
            confirm = input(get_message('warning_format', lang, usb_disk)).lower()
            if confirm in ('s', 'y'):  # Accept both Spanish and English confirmations
                break
        print(get_message('disk_invalid', lang))
    
    # Get USB name with default
    default_name = "WINUSB"
    usb_name = input(get_message('enter_name', lang, default_name)).strip()
    if not usb_name:
        usb_name = default_name
    
    return usb_disk, iso_path, usb_name

def main():
    check_root()
    lang = select_language()
    usb_disk, iso_path, usb_name = get_user_inputs(lang)
    
    unmount_usb(usb_disk)
    erase_usb(usb_disk, usb_name)
    mount_point = mount_iso(iso_path)
    copy_files(mount_point, usb_disk, usb_name)
    detach_iso(mount_point)
    eject_usb(usb_disk)
    print(get_message('process_complete', lang))

if __name__ == "__main__":
    main()
