import os
import re
import sys

def reassemble_files(directory):
    files_data = []
    
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                # Find the index in the comment at the end (e.g., //file123)
                match = re.search(r'//file(\d+)', content)
                if match:
                    index = int(match.group(1))
                    files_data.append((index, content))

    # Sort by the index
    files_data.sort(key=lambda x: x[0])
    
    # Concatenate content
    full_content = ""
    for _, content in files_data:
        # Remove the //file... comment line
        lines = content.splitlines()
        cleaned_lines = [line for line in lines if not line.strip().startswith("//file")]
        full_content += "\n".join(cleaned_lines)

    print(full_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 lmezard_ftp.py <directory>")
        sys.exit(1)
    
    reassemble_files(sys.argv[1])
