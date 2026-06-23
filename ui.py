"""
UI module for the Encrypted Journal CLI.
Handles banners, typing effects, and formatted output.
"""

import time
import sys
from colorama import Fore, Back, Style, init
from typing import Dict, List
import config

# Initialize colorama
init(autoreset=True)


def show_banner():
    """Display the fsociety-style ASCII banner for DeepVault."""
    banner = """
                                                                     ,,         
`7MM`7MYb.                          `7MMF'   `7MF'                `7MM   mm    
  MM    `Yb.                           `MA     ,V                    MM   MM    
  MM     `Mb  .gP"Ya   .gP"Ya `7MMpdMAo.VM:   ,V ,6"Yb.`7MM  `7MM    MM mmMMmm  
  MM      MM ,M'   Yb ,M'   Yb  MM   `Wb MM.  M'8)   MM  MM    MM    MM   MM    
  MM     ,MP 8M'''''' 8M''''''  MM    M8 `MM A'  ,pm9MM  MM    MM    MM   MM    
  MM    ,dP' YM.    , YM.    ,  MM   ,AP  :MM;  8M   MM  MM    MM    MM   MM    
.JMMmmmdP'    `Mbmmd'  `Mbmmd'  MMbmmd'    VF   `Moo9^Yo.`Mbod"YML..JMML. `Mbmo 
                                MM                                              
                              .JMML.                                            """
    
    print(Fore.CYAN + banner + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 80 + Style.RESET_ALL)
    print(Fore.GREEN + "Welcome to DeepVault - Encrypted Journal CLI" + Style.RESET_ALL)
    print(Fore.YELLOW + "=" * 80 + Style.RESET_ALL)


def type_out(text: str, delay: float = None):
    """
    Print text with a typing effect.
    
    Args:
        text: Text to print
        delay: Delay between characters (defaults to config.TYPING_DELAY)
    """
    if delay is None:
        delay = config.TYPING_DELAY
    
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def show_decrypting_animation(duration: float = 2.0):
    """Show a decrypting animation."""
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duration
    frame_idx = 0
    
    while time.time() < end_time:
        sys.stdout.write(f"\r{Fore.YELLOW}Decrypting journal... {frames[frame_idx % len(frames)]}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(0.1)
        frame_idx += 1
    
    sys.stdout.write(f"\r{Fore.GREEN}✓ Journal unlocked{' ' * 30}\n{Style.RESET_ALL}")


def prompt_passphrase(prompt_text: str = "Enter master passphrase: ") -> str:
    """
    Prompt for passphrase (hidden input).
    
    Args:
        prompt_text: Prompt message
        
    Returns:
        Entered passphrase
    """
    import getpass
    return getpass.getpass(Fore.CYAN + prompt_text + Style.RESET_ALL)


def prompt_command() -> str:
    """Prompt user for a command."""
    print(Fore.CYAN + "\nAvailable commands:" + Style.RESET_ALL)
    print(f"  {Fore.GREEN}new{Style.RESET_ALL} - Create new entry")
    print(f"  {Fore.GREEN}list{Style.RESET_ALL} - List all entries")
    print(f"  {Fore.GREEN}view <id-prefix>{Style.RESET_ALL} - View entry by ID")
    print(f"  {Fore.GREEN}search <query>{Style.RESET_ALL} - Search entries")
    print(f"  {Fore.GREEN}delete <id>{Style.RESET_ALL} - Delete entry")
    print(f"  {Fore.GREEN}panic{Style.RESET_ALL} - Secure wipe journal")
    print(f"  {Fore.GREEN}exit{Style.RESET_ALL} - Quit\n")
    
    return input(Fore.YELLOW + "deepvault> " + Style.RESET_ALL).strip()


def print_entry(entry: Dict):
    """
    Print a formatted entry.
    
    Args:
        entry: Entry dictionary
    """
    print(Fore.CYAN + f"\n{'='*60}" + Style.RESET_ALL)
    print(Fore.GREEN + f"ID: {Fore.WHITE}{entry['id']}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Title: {Fore.WHITE}{entry['title']}" + Style.RESET_ALL)
    print(Fore.GREEN + f"Date: {Fore.WHITE}{entry['timestamp']}" + Style.RESET_ALL)
    print(Fore.CYAN + f"{'-'*60}" + Style.RESET_ALL)
    print(entry['body'])
    print(Fore.CYAN + f"{'='*60}\n" + Style.RESET_ALL)


def print_entry_preview(entry: Dict):
    """
    Print a brief preview of an entry (for list view).
    
    Args:
        entry: Entry dictionary
    """
    print(Fore.GREEN + f"  [{entry['id'][:8]}...] " + 
          Fore.WHITE + f"{entry['title']:<30} " + 
          Fore.YELLOW + f"{entry['timestamp']}" + Style.RESET_ALL)


def print_entries_list(entries: List[Dict]):
    """
    Print list of entries.
    
    Args:
        entries: List of entry dictionaries
    """
    if not entries:
        print(Fore.YELLOW + "No entries found." + Style.RESET_ALL)
        return
    
    print(Fore.CYAN + f"\n{'Entries':<50}" + Style.RESET_ALL)
    print(Fore.CYAN + f"{'-'*70}" + Style.RESET_ALL)
    
    for entry in entries:
        print_entry_preview(entry)
    
    print(Fore.CYAN + f"{'-'*70}\n" + Style.RESET_ALL)


def print_error(message: str):
    """Print an error message."""
    print(Fore.RED + f"✗ Error: {message}" + Style.RESET_ALL)


def print_success(message: str):
    """Print a success message."""
    print(Fore.GREEN + f"✓ {message}" + Style.RESET_ALL)


def print_info(message: str):
    """Print an info message."""
    print(Fore.CYAN + f"ℹ {message}" + Style.RESET_ALL)
