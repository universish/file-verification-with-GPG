# File verification with GPG digital signature file (.asc , .sig)

File verification with gpg digital signature file. Quickly verifies files using digital signature files such as .asc .sig. It then issues a warning message. It indicates whether it is Trusted, Suspicious or Dangerous.
Running bash on Windows will automatically run the file-verify.py script.
It will then ask you to select the file you want to verify (for example .exe). Select it and click OK.
It will then ask you to select the digital verification file (for example .asc or .sig). Select it and click OK.
The results will appear. There are three results.
1. Safe: You can upload safely, you can use the file safely.
2. Suspicious: It's up to you whether to use it or not. If the signature is good, you can use it at your own risk. The file integrity is intact, but the Trust relationship may not have been established, i.e. the key that signed it may not be fully recognized on your system. If the signature is problematic, do not use it and delete it. The file may be malicious, or it may have been infiltrated, modified, or maliciously attacked. The file may have been modified. It may contain harmful content. And the responsibility lies with you. I do not accept responsibility, I refuse.
3. Dangerous: Never use the file and delete it. The file is very likely malware. After deleting it, scan your computer and network for malware.
The results are in Turkish. If you wish, you can support by translating.
The files you download are at your own risk and your own responsibility. I do not accept responsibility, I refuse.

--------------------------------------------------------------

## File Verification Tool - System Requirements

### 1. BASIC SOFTWARE
- Python 3.8+ (https://python.org/downloads/)
- GnuPG (GPG) 2.2+ 
  • Windows: https://gpg4win.org # GPG installation must be done manually.
  • Linux:   `sudo apt install gnupg`
  • Mac:     `brew install gnupg`

### 2. INSTALLATION CHECKS:
### A. Python PATH check:
   > python --version
   Python 3.x.x

### B. GPG PATH check:
   > gpg --version
   gpg (GnuPG) 2.x.x

### 3. SYSTEM SETTINGS
- Firewall: Allow port 11371 (for keyserver access)
- GPG configuration: gpg --keyserver keyserver.ubuntu.com --recv-keys 0x

### 4. TROUBLESHOOTING:
- "gpg not found": Add to PATH or reinstall
- The key could not be downloaded: Check Firewall/Proxy settings
- If you have a PATH problem: reinstall python and check 'add to PATH' in the installation or manually add to PATH or on Windows in terminal (powershell): 
`C:\<path_to_python.exe_file>\python.exe .\<file_name>.py`

### 5. Establishing requirements:
`pip install -r requirements.txt`

### 6. Install Thinker:
- python .py files additionally needs Thinker to run. If you don't have Thinker installed (it is usually installed with python):
Windows:
`winget install Python.Python.3 --override "/InstallAllUsers=1 /AddToPath=1 /Include_tkinter=1"`
- Note: Tkinter is usually bundled with Python.

### 7. OPTIONAL PACKAGES (for Development)
- pyinstaller == 6.0.0  # To compile to EXE
- pillow == 10.0.0      # For visual operations


