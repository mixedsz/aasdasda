from keyauth import api
import os
import logging
import sys
import time
import readchar
import hashlib
import ssl
import aiohttp
from time import sleep
from datetime import datetime, UTC

# SSL certificate handling for aiohttp
try:
    import certifi
    SSL_CERT_FILE = certifi.where()
except ImportError:
    SSL_CERT_FILE = None


try:
    import platform
    import discord
    import inquirer
    import psutil
    from art import text2art
    from helpmodule import Clone
    from colorama import Fore, Style
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress
    from rich.table import Table
    import asyncio
    import traceback
    from pytz import UTC
    import ctypes
except ImportError as e:
    print(f"{Fore.RED}Missing required library: {e.name}. Please install it using pip.{Style.RESET_ALL}")
    sys.exit(1)

# ✅ Function to clear the console
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# ✅ Get checksum of the executable for validation
def getchecksum():
    md5_hash = hashlib.md5()
    with open(sys.argv[0], "rb") as file:
        md5_hash.update(file.read())
    return md5_hash.hexdigest()

keyauthapp = api(
    name = "Reliant Server Cloner", # App name 
    ownerid = "Bv200ABmNA", # Account ID
    version = "1.0", # Application version. Used for automatic downloads see video here https://www.youtube.com/watch?v=kW195PLCBKs
    hash_to_check = getchecksum()
)

# ✅ Path for license storage
LICENSE_FILE = "license.txt"

def login_with_license():
    """ Handles license-only login and saves the license key. """
    clear()
    
    # ✅ Check if license.txt exists
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as file:
            license_key = file.read().strip()
        print(f"Using stored license: {license_key}")
    else:
        license_key = input("Enter your license key: ").strip()
    
    # ✅ Attempt to login
    try:
        keyauthapp.license(license_key)
        print("\n✅ Login successful!")
        
        # ✅ Save license key if it's new
        with open(LICENSE_FILE, "w") as file:
            file.write(license_key)
    
    except Exception as e:
        print(f"\n❌ Login failed: {e}")
        if os.path.exists(LICENSE_FILE):
            os.remove(LICENSE_FILE)  # ✅ Remove invalid license
        time.sleep(2)
        login_with_license()  # ✅ Retry


def clear():
    title = "Server Cloner | Reliant Services | https://t.me/reliantservices | https://reliant.mysellauth.com/"

    if platform.system() == 'Windows':
        os.system('cls')  # Clear console
        ctypes.windll.kernel32.SetConsoleTitleW(title)  # Set title in Windows
    elif platform.system() == 'Linux' or platform.system() == 'Darwin':
        os.system('clear')  # Clear terminal
        sys.stdout.write(f"\033]0;{title}\007")  # Set terminal title
        sys.stdout.flush() 

# Call function to clear and set the title
clear()

# Display Title Function
def display_title():
    # Initialize the console
    console = Console()

    # Title text
    title = "Reliant Server Cloner V.2.0.0"

    # Create a Text object and align it
    title_text = Text(title, style="bold blue")
    title_text.justify = "center"  # Center the text

    # Create a Panel with the aligned text
    panel = Panel(title_text, width=120)

    # Print the panel with the centered title
    console.print(panel)

# Display the title at the start
display_title()

def loading(seconds: int) -> None:
    """
    Display a progress bar for the specified number of seconds.
    
    Args:
        seconds (int): Duration for the progress bar in seconds.
    """
    with Progress() as progress:
        task = progress.add_task("Loading...", total=seconds)
        while not progress.finished:
            progress.update(task, advance=1)
            time.sleep(1)

def get_user_preferences() -> dict:
    """
    Display the default cloning preferences and allow the user to reconfigure them.
    
    Returns:
        dict: A dictionary with cloning preferences.
    """
    # Default cloning preferences
    default_preferences = {
        'guild_edit': True,
        'channels_delete': True,
        'roles_create': True,
        'categories_create': True,
        'channels_create': True,
        'emojis_create': False
    }

    def map_boolean_to_string(value: bool) -> str:
        return "Yes" if value else "No"

    # Prepare a panel displaying the current settings
    panel_content = "\n".join([ 
        f"- Change server name and icon: {map_boolean_to_string(default_preferences['guild_edit'])}",
        f"- Delete destination server channels: {map_boolean_to_string(default_preferences['channels_delete'])}",
        f"- Clone roles: {map_boolean_to_string(default_preferences['roles_create'])}",
        f"- Clone categories: {map_boolean_to_string(default_preferences['categories_create'])}",
        f"- Clone channels: {map_boolean_to_string(default_preferences['channels_create'])}",
        f"- Clone emojis: {map_boolean_to_string(default_preferences['emojis_create'])}"
    ])

    # Display Preferences Panel
    display_title()  # Display title before preferences
    Console().print(Panel(panel_content, title="Config BETA", style="bold blue", width=70))

    # Ask if the user wants to reconfigure the default settings
    questions = [
        inquirer.List('reconfigure', message='Do you want to reconfigure the default settings?', choices=['Yes', 'No'], default='No')
    ]
    answers = inquirer.prompt(questions)

    if answers and answers.get('reconfigure') == 'Yes':
        config_questions = [
            inquirer.Confirm('guild_edit', message='Edit the server icon and name?', default=False),
            inquirer.Confirm('channels_delete', message='Delete the channels?', default=False),
            inquirer.Confirm('roles_create', message='Clone roles? (NOT RECOMMENDED TO DISABLE)', default=False),
            inquirer.Confirm('categories_create', message='Clone categories?', default=False),
            inquirer.Confirm('channels_create', message='Clone channels?', default=False),
            inquirer.Confirm('emojis_create', message='Clone emojis? (Recommended for solo cloning)', default=False)
        ]
        updated_preferences = inquirer.prompt(config_questions)
        if updated_preferences:
            default_preferences.update(updated_preferences)

    # Clear the screen before returning preferences
    os.system('cls' if os.name == 'nt' else 'clear')
    return default_preferences

def restart() -> None:
    """
    Restart the current Python script.
    """
    python_executable = sys.executable
    os.execv(python_executable, [python_executable] + sys.argv)

async def main_program():
    """
    Main function for handling user input, authentication, and cloning operations.
    """
    # Clear the console screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display title again at the beginning of the main process
    display_title()

    # Create SSL context with proper certificate handling
    ssl_context = ssl.create_default_context()
    if SSL_CERT_FILE:
        ssl_context.load_verify_locations(SSL_CERT_FILE)

    # Create custom aiohttp connector with SSL context
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    # Initialize Discord client with custom connector
    intents = discord.Intents.default()
    client = discord.Client(intents=intents, connector=connector)

    # Loop until valid token and server IDs are provided
    while True:
        token = input(f"{Style.BRIGHT}{Fore.MAGENTA}Insert your token to proceed:{Style.RESET_ALL}\n > ")
        guild_source = input(f"{Style.BRIGHT}{Fore.MAGENTA}Source server ID:{Style.RESET_ALL}\n > ")
        guild_dest = input(f"{Style.BRIGHT}{Fore.MAGENTA}Destination server ID:{Style.RESET_ALL}\n > ")
        os.system('cls' if os.name == 'nt' else 'clear')

        print(f"{Style.BRIGHT}{Fore.GREEN}The values you inserted are:")
        print(f"Token: {Fore.YELLOW}{'*' * len(token)}{Style.RESET_ALL}")
        print(f"Source Server ID: {Fore.YELLOW}{guild_source}{Style.RESET_ALL}")
        print(f"Destination Server ID: {Fore.YELLOW}{guild_dest}{Style.RESET_ALL}")

        confirm = input(f"{Style.BRIGHT}{Fore.MAGENTA}Are these values correct? (Y/N):{Style.RESET_ALL}\n > ")

        if confirm.upper() == 'Y' and guild_source.isnumeric() and guild_dest.isnumeric():
            break
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{Style.BRIGHT}{Fore.RED}Invalid input. Please re-enter values.{Style.RESET_ALL}")

    # Get cloning preferences from user (or use defaults)
    preferences = get_user_preferences()

    @client.event
    async def on_ready():
        """
        Called when the Discord client is ready.
        Executes the cloning operations based on user preferences.
        """
        try:
            start_time = time.time()
            Console().print(Panel("Authentication successful", style="bold green", width=50))
            loading(5)
            os.system('cls' if os.name == 'nt' else 'clear')

            # Retrieve guild objects using provided IDs
            guild_from = client.get_guild(int(guild_source))
            guild_to = client.get_guild(int(guild_dest))

            # Execute cloning operations according to user preferences
            if preferences.get('guild_edit'):
                await Clone.guild_edit(guild_to, guild_from)
            if preferences.get('channels_delete'):
                await Clone.channels_delete(guild_to)
            if preferences.get('roles_create'):
                await Clone.roles_create(guild_to, guild_from)
            if preferences.get('categories_create'):
                await Clone.categories_create(guild_to, guild_from)
            if preferences.get('channels_create'):
                await Clone.channels_create(guild_to, guild_from)
            if preferences.get('emojis_create'):
                await Clone.emojis_create(guild_to, guild_from)

            elapsed_time = time.time() - start_time
            print(f"{Style.BRIGHT}{Fore.BLUE}Cloning completed in {elapsed_time:.2f} seconds.{Style.RESET_ALL}")
            await client.close()
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
            traceback.print_exc()
            restart()

    # Start the Discord client
    try:
        await client.start(token)
    except discord.LoginFailure:
        print(f"{Fore.RED}Invalid token.{Style.RESET_ALL}")
        restart()


# Run the login function
login_with_license()

# After successful login, execute the main functionality
asyncio.run(main_program())

# Prevent the script from instantly closing
input("Press Enter to exit...")
