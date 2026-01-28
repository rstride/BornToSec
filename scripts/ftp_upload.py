import ftplib
import sys
import os

FTP_HOST = "192.168.64.3"
FTP_USER = "lmezard"
FTP_PASS = 'G!@M6f4Eatau{sF"'

def upload_file(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found locally.")
        return False
        
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        # Try Passive mode first
        ftp.set_pasv(True)
        
        print(f"Uploading {filename} to {filename}...")
        with open(filename, 'rb') as f:
            ftp.storbinary(f"STOR {filename}", f)
        print(f"Successfully uploaded {filename}")
        ftp.quit()
        return True
    except Exception as e:
        print(f"Error uploading {filename} with PASV: {e}")
        try:
            # Try Active mode
            ftp = ftplib.FTP(FTP_HOST)
            ftp.login(FTP_USER, FTP_PASS)
            ftp.set_pasv(False)
            print(f"Retrying {filename} upload with Active mode...")
            with open(filename, 'rb') as f:
                ftp.storbinary(f"STOR {filename}", f)
            print(f"Successfully uploaded {filename}")
            ftp.quit()
        except Exception as e2:
            print(f"Error uploading {filename} with Active mode: {e2}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ftp_upload.py <file>")
        sys.exit(1)
        
    upload_file(sys.argv[1])
