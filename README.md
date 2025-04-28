# Data Acquisition and Visualization Software

### Developed and updated: Harrison Teele, B.E. 2025, M.S. 2026

**A cross-platform PyQt5 application for real-time plotting and logging of analog sensor data sent over a serial (UART) link from an ESP/Arduino-style board**

## Features

- **Real-time plotting** of incoming values with a rolling 2-minute (variable) window  
- **Buffered data acquisition** (e.g. 100 Hz serial reads) decoupled from a slower plot update rate (e.g. 10 Hz)  
- **Auto-detect and refresh COM ports**
- **Selectable baud rates** via dropdown (9600–115200 baud)  
- **Start / Stop / Clear** controls for acquisition and display  
- **Save to CSV** (timestamps + values) including computed **mean**, **std dev**, and **variance** for statistical analysis
- **Dark “Fusion” style** for consistent look on Windows/macOS/Linux  
- Packaged with **PyInstaller** into a single executable (with custom icon)

## Planned Updates:

- **Plot-point tools** (viewing datapoint info.)
- **Gain controls**
- **Saved user settings for rolling time window, baud rate, etc**
- **File name settings**

## Prerequisites

- Python 3.7+  
- [PyQt5](https://pypi.org/project/PyQt5/)  
- [pyserial](https://pypi.org/project/pyserial/)  
- matplotlib, numpy, pytz  

Install via:

```bash
pip install -r requirements.txt 
