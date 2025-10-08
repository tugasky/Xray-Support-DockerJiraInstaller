# Docker Jira One-Click Installer for Xray Support

A comprehensive GUI application for installing Jira with Docker, featuring automatic updates and advanced configuration options.

## Features

- **One-Click Installation**: Install Jira 8.x, 9.x, 10.x, and 11.x with a single click
- **Docker Integration**: Automated Docker container setup and configuration
- **MySQL Support**: Built-in MySQL database setup for Jira 10+
- **Advanced Configuration**: Customize ports, container names, database settings, and more
- **Automatic Updates**: Self-updating application with GitHub integration
- **Progress Tracking**: Visual progress indicators and detailed logging
- **Xray Support**: Optimized for Xray testing framework integration

## Installation

### Option 1: Download Pre-built Executable
1. Go to the [Releases](https://github.com/tugasky/Xray-Support-DockerJiraInstaller/releases) page
2. Download the latest `jira_installer.exe` file
3. Run the executable

### Option 2: Run from Source
1. Ensure Python 3.7+ is installed
2. Clone this repository
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python jira_installer.py`

## Usage

1. **Basic Installation**:
   - Enter the desired Jira version (e.g., 10.0.0)
   - Click "Install Jira"
   - Follow the progress in the logs

2. **Advanced Installation**:
   - Enable "Advanced Mode" to access additional options
   - Configure custom ports, container names, MySQL settings
   - Customize JDBC driver versions

3. **Check for Updates**:
   - Click "Check for Updates" to see if a newer version is available
   - Follow prompts to download and install updates automatically

## Update System

The application includes a built-in update system that:

- **Checks for Updates**: Automatically detects new versions on GitHub
- **Safe Installation**: Creates backups before updating
- **Rollback Support**: Automatically restores previous version if update fails
- **Progress Tracking**: Shows download and installation progress

### Manual Update Process

If you need to create a new release:

1. **Update Version**: Edit `CURRENT_VERSION` in `jira_installer.py`
2. **Build Executable**: Run `python build.py`
3. **Create Release**: Upload the executable from `releases/v{version}/` to GitHub

## Requirements

### System Requirements
- Windows 10/11, macOS, or Linux
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Internet connection for downloading Jira images

### Python Dependencies
- tkinter (usually included with Python)
- requests (for update system)

## Configuration Options

### Jira Versions Supported
- **8.x**: Jira 8 with built-in database
- **9.x**: Jira 9 with built-in database
- **10.x**: Jira 10 with external MySQL database
- **11.x**: Jira 11 with external MySQL database

### Advanced Configuration
- Custom ports (default: 8080 for Jira 10+, 8081 for older versions)
- Custom container names
- MySQL database configuration
- JDBC driver versions
- Network settings

## Troubleshooting

### Docker Issues
- Ensure Docker Desktop is running
- Check that ports are not already in use
- Verify internet connection for image downloads

### Update Issues
- Check internet connection
- Ensure sufficient disk space for downloads
- Try manual download if automatic update fails

### Permission Issues
- Run as administrator if you encounter file permission errors
- Check antivirus software isn't blocking the application

## Development

### Building from Source
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller pyinstaller.spec

# Or use the build script
python build.py
```

### Project Structure
```
├── jira_installer.py      # Main application
├── pyinstaller.spec       # PyInstaller configuration
├── file_version_info.txt  # Version information
├── build.py              # Build automation script
├── jira.ico              # Application icon
└── README.md             # This file
```

## Support

For support and questions:
- Contact: João Silva (joao.silva@sembi.com)
- GitHub Issues: [Report bugs and feature requests](https://github.com/tugasky/Xray-Support-DockerJiraInstaller/issues)

## Credits

Developed by João Silva (joao.silva@sembi.com) for Xray Support team.

## License

This project is intended for internal use by Xray Support team.
