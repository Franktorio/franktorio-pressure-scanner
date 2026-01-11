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

## Installation (.exe)

1. Download latest release!
> https://github.com/Franktorio/franktorio-pressure-scanner/releases

2. Run the scanner and click `Start Scan` on the title bar

3. If the scanner isn't finding the log files, press `Set Log Dir` and select the folder where **Roblox writes the logs.**

## Installation (from code)

1. Clone the repository:
```bash
git clone https://github.com/Franktorio/franktorio-pressure-scanner
cd franktorio-pressure-scanner
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See [LICENSE](LICENSE) file for details.

## Version

Current Version: Check `config/vars.py` for the latest version number
