# Chapel Padel Booking

Automated court booking for Chapel Allerton Tennis Club (Padel Courts) using Selenium.

## Overview
This project automates the process of booking padel courts at Chapel Allerton Tennis Club via their online booking system. It handles login, court and date selection, player entry, terms acceptance, and booking confirmation, providing robust error handling and clear success/failure reporting.

## Features
- Automated login via modal (not browser popup)
- Court type and date selection
- Player entry with robust error handling
- Automatic handling of Terms & Conditions
- Booking confirmation and receipt detection
- Clear console output for each step

## Requirements
- Python 3.8+
- Google Chrome browser
- ChromeDriver (matching your Chrome version)
- Selenium Python package

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
4. Download the correct version of ChromeDriver and ensure it is in your PATH.

## Configuration
- Edit `chapel_booking.py` to set your login credentials and player names.
- Ensure the player list and court preferences are up to date.

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

## Versioning
This is version **1.0.0** of the project.

## License
MIT License (add LICENSE file if required)

## Disclaimer
This project is not affiliated with Chapel Allerton Tennis Club. Use at your own risk and ensure compliance with club policies. 