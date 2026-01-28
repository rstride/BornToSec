import ftplib
import sys

FTP_HOST = "192.168.64.3"
FTP_USER = "lmezard"
FTP_PASS = 'G!@M6f4Eatau{sF"'

def download_file(filename):
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        # Try Passive mode first (default)
        ftp.set_pasv(True)
        
        print(f"Downloading {filename}...")
        with open(filename, 'wb') as f:
            ftp.retrbinary(f"RETR {filename}", f.write)
        print(f"Successfully downloaded {filename}")
        ftp.quit()
        return True
    except Exception as e:
        print(f"Error downloading {filename} with PASV: {e}")
        try:
            # Try Active mode
            ftp = ftplib.FTP(FTP_HOST)
            ftp.login(FTP_USER, FTP_PASS)
            ftp.set_pasv(False)
            print(f"Retrying {filename} with Active mode...")
            with open(filename, 'wb') as f:
                ftp.retrbinary(f"RETR {filename}", f.write)
            print(f"Successfully downloaded {filename}")
            ftp.quit()
        except Exception as e2:
            print(f"Error downloading {filename} with Active mode: {e2}")
            return False

if __name__ == "__main__":
    download_file("fun")
    download_file("README")
