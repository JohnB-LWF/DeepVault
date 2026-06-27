# DeepVault - Encrypted Journal CLI

```
                                                                    ,,         
`7MM`7MYb.                          `7MMF'   `7MF'                `7MM   mm    
  MM    `Yb.                           `MA     ,V                    MM   MM    
  MM     `Mb  .gP"Ya   .gP"Ya `7MMpdMAo.VM:   ,V ,6"Yb.`7MM  `7MM    MM mmMMmm  
  MM      MM ,M'   Yb ,M'   Yb  MM   `Wb MM.  M'8)   MM  MM    MM    MM   MM    
  MM     ,MP 8M'''''' 8M''''''  MM    M8 `MM A'  ,pm9MM  MM    MM    MM   MM    
  MM    ,dP' YM.    , YM.    ,  MM   ,AP  :MM;  8M   MM  MM    MM    MM   MM    
.JMMmmmdP'    `Mbmmd'  `Mbmmd'  MMbmmd'    VF   `Moo9^Yo.`Mbod"YML..JMML. `Mbmo 
                                MM                                              
                              .JMML.                                            
```

A secure, command-line encrypted journal application with military-grade AES-256 encryption. Designed for privacy-conscious users who want complete control over their personal journal data. I decided to create this application in my free time to experiment with encryption using Python, the programming language I am studying in college.

## Features

- **AES-256-GCM Encryption**: Military-grade authenticated encryption for all journal entries
- **Strong Key Derivation**: PBKDF2-SHA256 with 480,000 iterations for passphrase-based key generation
- **Local Storage Only**: All data stored locally—nothing leaves your machine
- **Full Encryption**: Entire journal file is encrypted; no metadata leakage
- **Authenticated Encryption**: GCM mode ensures data integrity; tampered files are rejected
- **Hacker Aesthetic**: Mr. Robot-inspired terminal UI with ASCII art banner
- **Easy-to-Use CLI**: Intuitive command interface for managing journal entries
- **Panic Wipe**: Secure file deletion option for emergency scenarios
- **Search Capability**: Full-text search across all journal entries

## Security Design

### Encryption

- **Algorithm**: AES-256 in GCM mode (authenticated encryption with associated data)
- **Key Derivation**: PBKDF2-SHA256 with a random salt and 480,000 iterations
- **Salt Length**: 256 bits (32 bytes)
- **IV Length**: 128 bits (16 bytes, unique per encryption)
- **Security**: Uses the `cryptography` library with hardware-accelerated implementations

### Data Storage

The journal is stored as a single encrypted blob containing:

```json
{
  "salt": "hex-encoded salt",
  "entries": [
    {
      "id": "unique-uuid",
      "title": "Entry Title",
      "timestamp": "ISO8601 timestamp",
      "body": "Entry content"
    }
  ]
}
```

### Security Notes

- **No plaintext storage**: Entries only exist in memory during operation
- **Passphrase-only**: The passphrase is never stored; only the derived key is used
- **Authenticated encryption**: GCM mode detects any unauthorized modifications
- **Secure wipe**: Panic option overwrites the file with random data before deletion
- **OS-level caveat**: Secure erase depends on filesystem type; SSDs may not guarantee complete erasure

## Installation

### Prerequisites

- Python 3.8+
- `pip` package manager

### Setup

1. Clone or download the project:

```bash
cd encrypted-journal-cli
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python journal.py
```

## Usage

### Starting the Application

```bash
python journal.py
```

You'll be prompted for a master passphrase. If it's your first time, a new journal will be created automatically.

### Commands

#### Create a New Entry

```
deepvault> new
Entry title: My First Secret
Enter your journal entry (press Enter for new lines, Ctrl+Enter to save and close):
This is the body of my journal entry...
✓ Entry added and saved!
```

#### List All Entries

```
deepvault> list
Entries
──────────────────────────────────────────────────────────────────
  [abc12345...] My First Secret                  2026-06-22T14:30:00
  [def67890...] Important Memory                 2026-06-21T10:15:30
──────────────────────────────────────────────────────────────────
```

#### View an Entry

```
deepvault> view abc12345-1234-1234-1234-123456789abc
```

You can also use a unique ID prefix shown in the list output.

#### Search Entries

```
deepvault> search memory
Found 2 matching entries:
  [def67890...] Important Memory                 2026-06-21T10:15:30
```

#### Delete an Entry

```
deepvault> delete abc12345-1234-1234-1234-123456789abc
Are you sure you want to delete: My First Secret?
Type 'yes' to confirm: yes
✓ Entry deleted and changes saved!
```

#### Panic Wipe

```
deepvault> panic
⚠ WARNING: This will permanently delete your encrypted journal!
Type 'PANIC' to confirm: PANIC
✓ Journal securely wiped!
```

#### Exit

```
deepvault> exit
✓ Goodbye!
```

## File Structure

```
encrypted-journal-cli/
├── README.md                # This file
├── requirements.txt         # Python dependencies
├── config.py               # Configuration and constants
├── crypto_utils.py         # Encryption/decryption utilities
├── storage.py              # Journal file I/O
├── ui.py                   # Terminal UI and formatting
└── journal.py              # Main CLI application
```

## Python Requirements

- **cryptography** (v42.0.0+): For AES-256-GCM and PBKDF2
- **colorama** (v0.4.6+): For colored terminal output

## Project Structure

### Modules

- **config.py**: Central configuration—journal path, encryption parameters, and defaults
- **crypto_utils.py**: Low-level cryptographic operations (key derivation, encrypt, decrypt)
- **storage.py**: High-level journal management (load, save, add, delete, search)
- **ui.py**: Terminal UI—banners, menus, formatting, and user prompts
- **journal.py**: Main CLI loop and command handlers

## Security Considerations for Deployment

- **Memory Exposure**: Passphrases and plaintext entries exist in memory during operation. Use trusted environments.
- **Filesystem Security**: Rely on OS-level file permissions; consider full-disk encryption for additional security.
- **Secure Erase Limitations**: The panic wipe is a basic overwrite. For high-security scenarios, consider DBAN or cryptographic erasure (encrypt before deletion).
- **Backup**: Store encrypted journal backups securely; remember your passphrase is the only recovery method.

## Portfolio Highlights

This project demonstrates:

- **Cryptographic best practices**: PBKDF2 with high iteration count, AES-256-GCM
- **Secure Python development**: Proper use of the `cryptography` library
- **CLI design**: Intuitive command interface with error handling
- **Modular architecture**: Clean separation of concerns (crypto, storage, UI, main)
- **User experience**: Colored output, typing effects, and helpful prompts

## License

This is an educational project. Use for learning and personal use.

## Disclaimer

DeepVault is designed for educational purposes and personal journaling on local machines. While it implements industry-standard encryption, it comes with no guarantees. Users are responsible for their own security practices, including:

- Choosing strong passphrases
- Securing their devices
- Maintaining backups of encrypted files
- Understanding OS-level security limitations

*For critical data, please consider consulting security professionals and using already established solutions.*

## About

DeepVault is inspired by my cybersecurity journey and the aesthetic of shows like *Mr. Robot*. It's a project meant to demonstrate how to build a secure CLI application in Python with proper cryptographic foundations.
