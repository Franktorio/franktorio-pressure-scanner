# Franktorio Pressure Scanner

A PyQt5-based desktop application that monitors Roblox game logs and looks for room data in real-time.
This tool allows you view what the researchers have documented in https://github.com/Franktorio/franktorio-xsouls-lab and see information of rooms in real time

## Features
- **Real-time Log Monitoring**: Automatically detects and monitors the latest Roblox log files
- **Room Detection**: Identifies and tracks room encounters during gameplay.
- **Image Support**: Downloads and displays the room images documented by researchers.
- **Information Support**: Allows you to see anything relevant documented by the researchers like hiding spots or easter eggs. Good for new players.
- **Version Checking**: Ensures you're running the latest version of the scanner

## Showcase

![Scanner Screenshot 1](https://pub-14908be79b544ff094192d7ae647f32b.r2.dev/Screenshot%202026-01-05%20011142.png)

![Scanner Screenshot 2](https://pub-14908be79b544ff094192d7ae647f32b.r2.dev/Screenshot%202026-01-10%20202239.png)

## Installation

### Windows

1. Download the latest Windows release:
> https://github.com/Franktorio/franktorio-pressure-scanner/releases

2. Run `Franktorio Research Scanner v1.4.6`

3. Click `Start Scan` on the title bar

4. If the scanner isn't finding the log files, press `Set Log Dir` and select the folder where **Roblox writes the logs**
   - Default Windows location: `%LOCALAPPDATA%\Roblox\logs`

### macOS

1. Download the latest macOS release:
> https://github.com/Franktorio/franktorio-pressure-scanner/releases

2. Run `Franktorio Research Scanner v1.4.6` (you may need to right-click and select "Open" for the first run)

3. Click `Start Scan` on the title bar

4. If the scanner isn't finding the log files, press `Set Log Dir` and select the folder where **Roblox writes the logs**
   - Default macOS location: `~/Library/Logs/Roblox`

### Linux

1. Download the latest Linux release:
> https://github.com/Franktorio/franktorio-pressure-scanner/releases

2. Make the file executable:
```bash
chmod +x franktorio-research-scanner
```

3. Run the application:
```bash
./franktorio-research-scanner
```

4. Click `Start Scan` on the title bar

5. If the scanner isn't finding the log files, press `Set Log Dir` and select the folder where **Roblox writes the logs**

**NOTES:** 
- **SCANNER WILL ALWAYS READ THE LATEST LOG FILE, IF YOU ARE NOT IN A GAME IT WILL READ THE LATEST FILE IT CAN. FOR A BETTER EXPERIENCE, JOIN A GAME FIRST BEFORE STARTING SCAN**
- **STARTING SCANNER, STOPPING SCANNER AND RESTARTING SCANNER WITHOUT LEAVING A GAME WILL CAUSE THE SCANNER TO START READING THE ENTIRE FILE FROM THE BEGINNING**

## Installation (from code)

1. Clone the repository:
```bash
git clone https://github.com/Franktorio/franktorio-pressure-scanner
cd franktorio-pressure-scanner
```

2. Install required dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the application:

**Windows:**
```bash
python main.py
```

**Linux/macOS:**
```bash
./main.py
```
or
```bash
python main.py
```

### Building Executable (Optional)

If you want to build your own executable:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:

**Windows:**
```bash
pyinstaller --onefile --windowed main.py --name=franktorio-research-scanner --icon=config/images/researchfrankbadge.png --add-data "config/images;config/images"
```

**macOS:**
```bash
pyinstaller --windowed main.py --name=franktorio-research-scanner --icon=config/images/researchfrankbadge.icns --add-data "config/images:config/images"
```

**Linux:**
```bash
pyinstaller --onefile main.py --name=franktorio-research-scanner --add-data "config/images:config/images"
```

The built executable will be located in the `dist/` folder.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See [LICENSE](LICENSE) file for details.

## Version

Current Version: Check `config/vars.py` for the latest version number
