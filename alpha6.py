import os
import shutil
import requests
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5

def get_game_directory():
    while True:
        game_dir = input("Enter the path to the '\ZenlessZoneZero Game' directory: ").strip()
        data_dir = os.path.join(game_dir, "ZenlessZoneZero_Data")
        if os.path.isdir(game_dir) and os.path.isdir(data_dir):
            return game_dir
        else:
            print("Invalid path. Please try again...")

def save_game_directory(game_dir):
    os.makedirs('main', exist_ok=True)
    with open('main/game_directory.txt', 'w') as f:
        f.write(game_dir)
        print(f'Directory saved to \main\game_directory.txt')

def load_game_directory():
    try:
        with open('main/game_directory.txt', 'r') as f:
            game_dir = f.read().strip()
            data_dir = os.path.join(game_dir, "ZenlessZoneZero_Data")
            if os.path.isdir(game_dir) and os.path.isdir(data_dir):
                return game_dir
            else:
                print("Saved directory is not valid. Please enter a new path.")
                new_game_dir = get_game_directory()
                save_game_directory(new_game_dir)
                return new_game_dir
    except FileNotFoundError:
        new_game_dir = get_game_directory()
        save_game_directory(new_game_dir)
        return new_game_dir

def find_required_files(game_dir):
    persistent_dir = os.path.join(game_dir, "ZenlessZoneZero_Data", "Persistent")
    required_files = [
        "audio_version_remote",
        "data_version_remote",
        "res_version_remote",
        "silence_version_remote"
    ]
    found_files = [file for file in required_files if os.path.isfile(os.path.join(persistent_dir, file))]
    return found_files, persistent_dir

def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def load_private_key_from_pem_file(filename):
    with open(filename, 'r') as pem_file:
        private_key = RSA.importKey(pem_file.read())
    return private_key

def decrypt_value(encrypted_value_base64, private_key):
    encrypted_buffer = base64.b64decode(encrypted_value_base64)
    cipher = Cipher_PKCS1_v1_5.new(private_key)
    
    decrypted_parts = []
    block_size = private_key.size_in_bytes()
    
    for i in range(0, len(encrypted_buffer), block_size):
        block = encrypted_buffer[i:i + block_size]
        decrypted_block = cipher.decrypt(block, None)
        decrypted_parts.append(decrypted_block)
    
    decrypted_value = b''.join(decrypted_parts).decode('utf8')
    return decrypted_value

def save_to_txt_file(filename, data):
    with open(filename, 'w') as txt_file:
        txt_file.write(data)
    print(f'Data saved to {filename}')

def retry_prompt(message):
    input(message + " Press Enter to try again...")

while True:
    try:
        with open('main/url.txt', 'r') as file:
            url = file.readline().strip()
            
        data = fetch_data(url)
        break
    except (requests.exceptions.RequestException, FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Error fetching data: {e}')
        retry_prompt("Error fetching data.")
        
while True:
    try:
        pem_file_path = 'main/key.pem'
        
        private_key = load_private_key_from_pem_file(pem_file_path)
        break
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading key: {e}')
        retry_prompt("Error loading key.")

while True:
    try:
        encrypted_value_base64 = data.get('content')
        if not encrypted_value_base64:
            raise KeyError('Key "content" not found in the JSON data')
        
        decrypted_value = decrypt_value(encrypted_value_base64, private_key)
        print('Successfully decrypted value')
        break
    except (KeyError, ValueError, TypeError) as e:
        print(f'Error decrypting value: {e}')
        retry_prompt("Error decrypting value.")

output_txt_file = 'main/decrypted_data.txt'
save_to_txt_file(output_txt_file, decrypted_value)

decrypted_data_file = 'main/decrypted_data.txt'
output_file = 'main/revision_number.txt'

try:
    with open(decrypted_data_file, 'r') as file:
        data = json.load(file)
    
    cdn_conf_ext = data.get('cdn_conf_ext', {})
    design_data = cdn_conf_ext.get('design_data', {})
    game_res = cdn_conf_ext.get('game_res', {})
    silence_data = cdn_conf_ext.get('silence_data', {})
    
    data_revision = design_data.get('data_revision', 'N/A')
    res_revision = game_res.get('res_revision', 'N/A')
    silence_revision = silence_data.get('silence_revision', 'N/A')
    audio_revision = game_res.get('audio_revision', 'N/A')
    
    content = (
        f"audio_revision: {audio_revision}\n"
        f"data_revision: {data_revision}\n"
        f"res_revision: {res_revision}\n"
        f"silence_revision: {silence_revision}\n"
    )
    
    with open(output_file, 'w') as file:
        file.write(content)
    
    print(f'Revision numbers saved to {output_file}')

except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
    print(f'Error: {e}')

def delete_persist_files(persistent_dir):
    for file in os.listdir(persistent_dir):
        if file.endswith("_persist") and file.replace("_persist", "_remote") in os.listdir(persistent_dir):
            os.remove(os.path.join(persistent_dir, file))

def rename_remote_files(persistent_dir):
    for file in os.listdir(persistent_dir):
        if file.endswith("_remote"):
            os.rename(os.path.join(persistent_dir, file), os.path.join(persistent_dir, file.replace("_remote", "_persist")))

def delete_revision_files(persistent_dir):
    revision_files = [
        "audio_revision",
        "data_revision",
        "res_revision",
        "silence_revision"
    ]
    for file in revision_files:
        file_path = os.path.join(persistent_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

def create_revision_files(persistent_dir):
    with open('main/revision_number.txt', 'r') as f:
        lines = f.readlines()
        for line in lines:
            key, value = line.strip().split(": ")
            filename = f"{key}.txt"
            with open(os.path.join(persistent_dir, filename), 'w') as revision_file:
                revision_file.write(value)

def rename_revision_files(persistent_dir):
    for file in os.listdir(persistent_dir):
        if file.endswith("_revision.txt"):
            os.rename(os.path.join(persistent_dir, file), os.path.join(persistent_dir, file.replace(".txt", "")))

def main():
    game_dir = load_game_directory()
    if not game_dir:
        game_dir = get_game_directory()
        save_game_directory(game_dir)

    found_files, persistent_dir = find_required_files(game_dir)
    while not found_files:
        choice = input("No required files found!. Press Enter to search again...").strip().lower()
        save_game_directory(game_dir)
        found_files, persistent_dir = find_required_files(game_dir)

    delete_persist_files(persistent_dir)
    rename_remote_files(persistent_dir)
    delete_revision_files(persistent_dir)
    create_revision_files(persistent_dir)
    rename_revision_files(persistent_dir)

    print("Patch success!. Press enter to exit.")
    input()

if __name__ == "__main__":
    main()
