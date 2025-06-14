# Chapel Padel Booking

Automated court booking for Chapel Allerton Tennis Club (Padel Courts) using Selenium.

## Overview
This project automates the process of booking padel courts at Chapel Allerton Tennis Club via their online booking system. It handles login, court and date selection, player entry, terms acceptance, and booking confirmation, providing robust error handling and clear success/failure reporting.

## Features
- Automated login via modal (not browser popup)
- Court type and date selection (dynamic, via .env)
- Player entry with robust error handling
- Automatic handling of Terms & Conditions
- Booking confirmation and receipt detection
- Clear console output for each step
- **Works with Selenium Grid (Docker) for remote browser automation**
- **Graceful error handling for unavailable/duplicate bookings**
- **Debug output, screenshots, and HTML dumps for troubleshooting**
- **Configurable via .env file (not committed for security)**

## Requirements
- Python 3.8+
- Google Chrome browser (or compatible with Selenium Grid)
- ChromeDriver (matching your Chrome version, or Selenium Grid Docker container)
- Selenium Python package
- (Optional) Docker for running Selenium Grid

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/chapel-padel-booking.git
   cd chapel-padel-booking
   ```
2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install selenium
   ```
4. Download the correct version of ChromeDriver and ensure it is in your PATH, or set up Selenium Grid with Docker.

## Configuration
- Copy `.env.example` to `.env` and fill in your login credentials, player names, court type, date, and time.
- **Do not commit your `.env` file to version control.**
- The script reads all configuration from `.env` (no need to edit `chapel_booking.py`).

## Usage
Run the booking script:
```bash
python chapel_booking.py
```
The script will:
- Log in to the Chapel Allerton booking site
- Select the desired court type and date
- Enter up to three unique player names
- Accept Terms & Conditions
- Confirm the booking and print the receipt/confirmation
- Save debug screenshots and HTML if errors occur
- Gracefully handle unavailable or duplicate bookings (with clear log output)

### Using Selenium Grid (Docker)
- Start Selenium Grid with Docker (see Selenium docs for details)
- Set the remote driver URL in your `.env` file (e.g., `SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub`)
- The script will use the remote driver automatically if configured

## Versioning
This is version **1.2.0** of the project.

## Changelog
### v1.2.0
- Selenium Grid (Docker) support for remote browser automation
- .env-based configuration for credentials, court, date, time, and players
- Robust error handling for unavailable/duplicate bookings
- Debug output, screenshots, and HTML dumps for troubleshooting
- No sensitive data committed to the repo

## License
MIT License (add LICENSE file if required)

## Disclaimer
This project is not affiliated with Chapel Allerton Tennis Club. Use at your own risk and ensure compliance with club policies. 