# Docker Jira One-Click Installer for Xray Support

A GUI application for installing Jira with Docker, featuring one-click installation and Xray testing framework optimization.

## Features

- **One-Click Installation**: Install Jira 8.x, 9.x, 10.x, and 11.x with a single click
- **Docker Integration**: Automated container setup and configuration
- **MySQL Support**: Built-in database setup for Jira 10+
- **Advanced Configuration**: Custom ports, container names, and database settings
- **Automatic Updates**: Self-updating application with GitHub integration
- **Progress Tracking**: Visual indicators and detailed logging
- **Xray Support**: Optimized for Xray testing framework integration

## Installation

### Quick Install
1. Download `jira_installer.exe` from the [Releases](https://github.com/tugasky/Xray-Support-DockerJiraInstaller/releases) page
2. Run the executable

### From Source
```bash
pip install -r requirements.txt
python jira_installer.py
```

## Usage

1. Enter Jira version (e.g., 10.0.0)
2. Click "Install Jira"
3. Monitor progress in the logs

For advanced options, enable "Advanced Mode" to configure custom settings.

## Requirements

- **System**: Windows 10/11, macOS, or Linux
- **Docker**: Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- **Internet**: Required for downloading Jira images
- **Python**: 3.7+ with tkinter and requests (for source installation)

## Jira Versions Supported

- **8.x & 9.x**: Built-in database
- **10.x & 11.x**: External MySQL database

## Troubleshooting

### Common Issues
- **Docker not running**: Ensure Docker Desktop is started
- **Port conflicts**: Check if ports 8080/8081 are available
- **No internet**: Required for downloading Jira Docker images
- **Permission errors**: Run as administrator if needed

### Windows DLL Issues
If you encounter "failed to load python dll" errors:
- Install latest Microsoft Visual C++ Redistributables
- Use Python 3.7-3.11
- Add executable to antivirus exclusions

## Support

For support and questions:
- Contact: João Silva (joao.silva@sembi.com)
- GitHub Issues: [Report bugs and feature requests](https://github.com/tugasky/Xray-Support-DockerJiraInstaller/issues)

## License

This project is intended for internal use by Xray Support team.
