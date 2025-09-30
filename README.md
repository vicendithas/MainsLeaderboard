
# MainsLeaderboard

MainsLeaderboard is a program designed to keep track of which Pokemon have been used playing *Pokemon* over time. It simply keeps track of the Pokemon, where you obtained it, and what date you caught it, and displays basic statistics. These include an overall leaderboard organized by the amount of times ran (by default), the last 10 Pokemon that were ran, and the spread of where you found the Pokemon.

![Leaderboard Example](https://raw.githubusercontent.com/sk84uhlivin/MainsLeaderboard/refs/heads/main/leaderboard.png)


# Installation

This program can be installed and run via an executable (Windows), or directly from the source code (Linux or Windows).

NOTICE: The release executables for this project are created with [pyinstaller](https://pyinstaller.org/en/stable/), which is used to convert Python projects into compiled executables. As this is a common way for bad actors to send malicious code in a disguised manner, many antivirus programs detect it as a virus, and will quarantine it. The releases for this project are built directly from the source code using GitHub Actions. If you do not trust my executables, please install and run from source instead. There's nothing I can immediately do to mitigate this, and apologize for the inconvenience.

## Executable

Download, and extract the latest release from [HERE](https://github.com/sk84uhlivin/MainsLeaderboard/releases).

## Source

Clone the repository with the following command:

`git clone https://github.com/sk84uhlivin/MainsLeaderboard.git`

Install the required dependencies. Use a virtual environment if you wish:

`cd MainsLeaderboard`

`pip install -r requirements.txt`


# Run

Double click the executable, or run `python3 server.py` if running from source, and navigate to one of the IP addresses shown in the terminal.

## Configure

You can edit the config.json file to change the leaderboard header and the port. If you want to run multiple leaderboards, you should change the second leaderboard's port (ex. 8081).

Each time a GIF is loaded onto the page, it has a (by default) 1/8192 chance of being shiny. If this happens, you'll get a message on the page that "A shiny Pokémon appeared". If you want to change these odds, they can be changed in the config.json file.

To choose the game's sprites/gifs that are used on the page, edit the "game" parameter in config.json. Valid options are:
- crystal
- emerald
- stadium2
- bw2


# Update

## Executable

Download, and extract the latest release from [HERE](https://github.com/sk84uhlivin/MainsLeaderboard/releases). Then, move the `pokemon_usage.csv` file, that's located in the same directory as the previous version, to the location of the latest version.

## Source

`git pull origin main`

# Usage

Simply enter the information asked for at the top of the page and hit "Add Entry" to add a Pokemon. Alternatively, or to correct any errors, you can edit the `pokemon_usage.csv` file directly, and refresh the page to show any changes.

> README written with [StackEdit](https://stackedit.io/).

