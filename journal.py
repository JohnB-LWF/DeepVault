"""
Main CLI entry point for the Encrypted Journal.
Ties together crypto, storage, and UI modules.
"""

import os
import sys
import traceback
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

import config
import crypto_utils
import storage
import ui


def _read_entry_body() -> str:
    """Read a multiline journal entry from the terminal."""
    print(
        ui.Fore.CYAN
        + "Enter your journal entry (press Enter for new lines, Ctrl+Enter to save and close):"
        + ui.Style.RESET_ALL
    )

    if os.name == "nt":
        import ctypes
        import msvcrt

        lines = []
        current_line = []
        get_async_key_state = getattr(ctypes.windll.user32, "GetAsyncKeyState", None)

        while True:
            char = msvcrt.getwch()

            if char in ("\r", "\n"):
                ctrl_down = bool(getattr(ctypes.windll.user32, "GetAsyncKeyState", lambda *_: 0)(0x11) & 0x8000)
                lines.append("".join(current_line))
                current_line = []
                print()

                if ctrl_down:
                    break

                continue

            if char == "\x08":
                if current_line:
                    current_line.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue

            if char in ("\x00", "\xe0"):
                msvcrt.getwch()
                continue

            current_line.append(char)
            sys.stdout.write(char)
            sys.stdout.flush()

        return "\n".join(lines).strip()

    lines = []

    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines).strip()


def init_new_journal(passphrase: str) -> dict:
    """Initialize a new journal."""
    journal = storage.initialize_journal()
    storage.save_journal(journal, passphrase)
    ui.print_success("New journal created and encrypted!")
    return journal


def load_or_create_journal(passphrase: str) -> dict | None:
    """Load existing journal or create new one."""
    try:
        journal = storage.load_journal(passphrase)
        ui.print_success("Journal decrypted successfully!")
        return journal
    except FileNotFoundError:
        ui.print_info("No existing journal found. Creating new one...")
        return init_new_journal(passphrase)
    except (InvalidTag, ValueError) as e:
        ui.print_error("Failed to decrypt journal. Wrong passphrase?")
        return None


def cmd_new(journal: dict, passphrase: str) -> dict:
    """Create a new entry."""
    print()
    title = input(ui.Fore.CYAN + "Entry title: " + ui.Style.RESET_ALL).strip()
    
    if not title:
        ui.print_error("Title cannot be empty!")
        return journal
    
    body = _read_entry_body()
    
    if not body:
        ui.print_error("Entry cannot be empty!")
        return journal
    
    journal = storage.add_entry(journal, title, body)
    storage.save_journal(journal, passphrase)
    ui.print_success("Entry added and saved!")
    return journal


def cmd_list(journal: dict) -> None:
    """List all entries."""
    ui.print_entries_list(journal["entries"])


def cmd_view(journal: dict, entry_id: str) -> None:
    """View a specific entry."""
    try:
        entry = storage.get_entry_by_id(journal, entry_id)
        ui.print_entry(entry)
    except ValueError as e:
        ui.print_error(str(e))


def cmd_search(journal: dict, query: str) -> None:
    """Search entries."""
    if not query:
        ui.print_error("Search query cannot be empty!")
        return
    
    results = storage.search_entries(journal, query)
    
    if results:
        print(ui.Fore.GREEN + f"Found {len(results)} matching entries:" + ui.Style.RESET_ALL)
        ui.print_entries_list(results)
    else:
        ui.print_info("No entries match your search.")


def cmd_delete(journal: dict, entry_id: str, passphrase: str) -> dict:
    """Delete an entry."""
    try:
        # Confirm deletion
        entry = storage.get_entry_by_id(journal, entry_id)
        print()
        print(ui.Fore.YELLOW + f"Are you sure you want to delete: {entry['title']}?" + ui.Style.RESET_ALL)
        confirm = input(ui.Fore.RED + "Type 'yes' to confirm: " + ui.Style.RESET_ALL).strip().lower()
        
        if confirm != "yes":
            ui.print_info("Deletion cancelled.")
            return journal
        
        journal = storage.delete_entry(journal, entry_id)
        storage.save_journal(journal, passphrase)
        ui.print_success("Entry deleted and changes saved!")
        return journal
    except ValueError as e:
        ui.print_error(str(e))
        return journal


def cmd_panic(passphrase: str) -> bool:
    """Securely wipe the journal file."""
    print()
    print(ui.Fore.RED + "⚠ WARNING: This will permanently delete your encrypted journal!" + ui.Style.RESET_ALL)
    confirm = input(ui.Fore.RED + "Type 'PANIC' to confirm: " + ui.Style.RESET_ALL).strip()
    
    if confirm != "PANIC":
        ui.print_info("Panic wipe cancelled.")
        return False
    
    try:
        if config.JOURNAL_PATH.exists():
            # Overwrite with random data before deletion (simple secure erase)
            file_size = config.JOURNAL_PATH.stat().st_size
            with open(config.JOURNAL_PATH, "wb") as f:
                f.write(os.urandom(file_size))
            
            os.remove(config.JOURNAL_PATH)
            ui.print_success("Journal securely wiped!")
            return True
        else:
            ui.print_error("Journal file not found.")
            return False
    except Exception as e:
        ui.print_error(f"Failed to wipe journal: {e}")
        return False


def main():
    """Main CLI loop."""
    try:
        # Show banner and animation
        ui.show_banner()
        ui.show_decrypting_animation(duration=1.5)
        
        # Get passphrase
        print()
        passphrase = ui.prompt_passphrase()
        
        if not passphrase:
            ui.print_error("Passphrase cannot be empty!")
            sys.exit(1)
        
        # Load or create journal
        print()
        journal = load_or_create_journal(passphrase)
        
        if journal is None:
            sys.exit(1)
        
        # Main command loop
        print()
        ui.print_success(f"Journal loaded with {len(journal['entries'])} entries.")
        
        while True:
            try:
                command = ui.prompt_command()
                
                if not command:
                    continue
                
                parts = command.split(None, 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd == "new":
                    journal = cmd_new(journal, passphrase)
                
                elif cmd == "list":
                    cmd_list(journal)
                
                elif cmd == "view":
                    if not args:
                        ui.print_error("Usage: view <entry_id>")
                    else:
                        cmd_view(journal, args)
                
                elif cmd == "search":
                    if not args:
                        ui.print_error("Usage: search <query>")
                    else:
                        cmd_search(journal, args)
                
                elif cmd == "delete":
                    if not args:
                        ui.print_error("Usage: delete <entry_id>")
                    else:
                        journal = cmd_delete(journal, args, passphrase)
                
                elif cmd == "panic":
                    if cmd_panic(passphrase):
                        ui.print_success("Exiting DeepVault.")
                        break
                
                elif cmd == "exit" or cmd == "quit":
                    ui.print_success("Goodbye!")
                    break
                
                else:
                    ui.print_error(f"Unknown command: {cmd}")
            
            except KeyboardInterrupt:
                print()
                ui.print_info("Interrupted. Type 'exit' to quit.")
            except EOFError:
                print()
                ui.print_success("End of input. Exiting DeepVault.")
                break
            except Exception as e:
                ui.print_error(f"An error occurred: {e}")
                traceback.print_exc()
    
    except KeyboardInterrupt:
        print()
        ui.print_success("Exiting DeepVault.")
        sys.exit(0)
    except Exception as e:
        ui.print_error(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
