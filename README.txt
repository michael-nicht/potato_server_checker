This app has been tested with Python 3.12 and Windows 11, older Python versions or other operating systems may not be compatible.

Setup:
1. Install Python 3
2. Run 'pip install -r requirements.txt' in powershell in the folder which contains the requirements.txt file
3. Open the settings.py file in notepad or some other text editor and enter your SteamID64, and optionally enter some regions that you don't want to see servers for

How to run (3 options):
- Double-click the main.py file
- Run 'python main.py' or 'pythonw main.py' in a terminal
- Use a desktop shortcut (see below)

Creating a desktop shortcut with an icon and no terminal popup:
1. Click on main.py, then shift + right-click it again and click Send To > Desktop (Create shortcut).
2. On the desktop right-click the new shortcut and click properties
3. Click Change Icon and browse to the 'images/potato.ico' file and click ok
4. In the "Target" text field of the shortcut put pythonw followed by a space in front of the file path to the main.py file that is already there
