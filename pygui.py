import time
import pytz 
import csv
import logging
import sys
import serial
import serial.tools.list_ports
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure 
from matplotlib.dates import *
from datetime import datetime, timedelta, date

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename = 'data_acquisition.log',
                    filemode='w'
                    )

class DataAcquisition(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(DataAcquisition, self).__init__(*args, **kwargs)
        self.setWindowTitle("Ricovr Data Acquisition Software")
        self.setWindowIcon(QIcon('ricovr_icon.png')) # FIXME: Icon not showing up
        self.setFixedSize(640, 480)

        layout = QHBoxLayout()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.x_data = []
        self.y_data = []
        self.serial_buffer = []

        self.initUI()

    def initUI(self):
        
        # ----------------- STYLESHEET -----------------

        app.setStyle(QStyleFactory.create("Fusion"))
        app.setStyleSheet("""
                        QPushButton {
                            color: white;
                        }
                        QComboBox{
                            color: white;
                          }
                    """)
 
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor("#3c3c3c"))
        dark_palette.setColor(QPalette.WindowText, QColor("#ffffff"))
        app.setPalette(dark_palette)

        # ----------------- TITLE & SUBTITLE -----------------

        # TITLE
        self.title = QLabel("Ricovr Data Acquisition & Visualization Software", self)
        self.title.setFont(QFont('Verdana', 24))
        self.title.setFixedWidth(640)
        self.title.move(30, 20)

        # SUBTITLE
        self.subtitle = QLabel("Harrison Teele - B.E. Computer Engineering '25, M.S. Physics '26", self)
        self.subtitle.setFont(QFont('Verdana', 14))
        self.subtitle.setFixedWidth(640)
        self.subtitle.move(90, 42)

        # ----------------- CONTROLS -----------------

        # COM DROPDOWN
        controls_layout = QHBoxLayout()
        self.com_dropdown = QComboBox(self)
        self.com_dropdown.setFixedWidth(250)
        self.com_dropdown.move(5,395)
        controls_layout.addWidget(self.com_dropdown)

        # BAUDRATE DROPDOWN
        self.baud_dropdown = QComboBox(self)
        self.baud_dropdown.setFixedWidth(160)
        self.baud_dropdown.move(5,428)
        controls_layout.addWidget(self.baud_dropdown)

        self.com_dropdown.currentIndexChanged.connect(self.on_com_change)
        self.baud_dropdown.currentIndexChanged.connect(self.on_baud_change)

        # START BTN
        start_button = QPushButton("Start", self)
        start_button.setToolTip("Starts data logging")
        start_button.move(255,395)
        start_button.setFixedWidth(75)
        start_button.clicked.connect(self.button_start)
        controls_layout.addWidget(start_button)

        # STOP BTN 
        stop_button = QPushButton("Stop", self)
        stop_button.setToolTip("Stops data logging")
        stop_button.move(330,395)
        stop_button.setFixedWidth(75)
        stop_button.clicked.connect(self.button_stop)
        controls_layout.addWidget(stop_button)

        # CLEAR BTN
        clear_button = QPushButton("Clear Plot", self)
        clear_button.setToolTip("Clears current plot")
        clear_button.move(405,395)
        clear_button.setFixedWidth(100)
        clear_button.clicked.connect(self.button_clear)
        controls_layout.addWidget(clear_button)

        # SAVE BTN
        save_button = QToolButton(self)
        save_button.setIcon(QIcon('save_icon.png'))
        save_button.setIconSize(QSize(20,20))
        save_button.setFixedSize(30,30)
        save_button.setAutoRaise(True)
        save_button.setToolTip("Save data to .csv")
        save_button.move(605,395)
        save_button.setStyleSheet("""
                                    QToolButton {
                                        background: transparent;
                                        border: none;
                                    }
                                    QToolButton:hover {
                                        background: rgba(0,0,0,0.1);
                                    }
                                """)
        save_button.clicked.connect(self.on_save)
        controls_layout.addWidget(save_button)

        # ----------------- INIT. FUNCTIONS -----------------

        self.com_port_check()
        self.init_com_ports()
        self.init_baudrates()
        self.init_plot()

        # ----------------- TIMERS -----------------

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.serial_timer = QTimer()
        self.serial_timer.timeout.connect(self.serial_read)

        self.est_tz = pytz.timezone("America/New_York")
        self.start_time = None

        self.show()

    def com_port_check(self):
        self.com_port_check = QTimer()
        self.com_port_check.timeout.connect(self.init_com_ports)
        self.com_port_check.start(1000)

    def init_com_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        update_list = [f"COM {i+1}: {port}" for i, port in enumerate(port_list)]
        active_list = [self.com_dropdown.itemText(i) for i in range(self.com_dropdown.count())]
        
        if update_list != active_list:
            previous_com = self.com_dropdown.currentText()
            self.com_dropdown.clear()
            self.com_dropdown.addItems(update_list)
            logging.info("COM Ports updated")
        
            if previous_com in update_list:
                i = update_list.index(previous_com)
                self.com_dropdown.setCurrentIndex(i)
            else:
                if self.com_dropdown.count() > 0:
                    self.com_dropdown.setCurrentIndex(0)
        
        try:
            self.com_dropdown.currentIndexChanged.disconnect()
        except:
            pass
    
    def init_baudrates(self):
        baudrates = ["9600", "19200", "38400", "57600", "115200"]
        baud_text = [f"Baudrate: {b}" for b in baudrates]
        self.baud_dropdown.addItems(baud_text)

        try:
            self.baud_dropdown.currentIndexChanged.disconnect()
        except:
            pass

    def on_com_change(self, i):
        current_port = self.com_dropdown.currentText()
        if": " in current_port:
            self.com_port = current_port.split(": ")[1]
        else:
            self.com_port = current_port
        logging.info("Selected COM:  ", self.com_port)

    def on_baud_change(self, i):
        current_baud = self.baud_dropdown.currentText()
        if ": " in current_baud:
            split_baud = current_baud.split(": ")[1]
            self.baudrate = int(split_baud)
        else:
            self.baudrate = int(current_baud)
        logging.info("Selected Baudrate: ", self.baudrate)

    def on_save(self):
        today = date.today()
        filename = today.strftime("%Y-%m-%d") + ".csv"
        std_dev = np.std(self.y_data)
        mean = np.mean(self.y_data)
        variance = np.var(self.y_data)
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Time Stamp", "Value", "Standard Deviation", "Mean", "Variance"])
            for t, val in zip(self.x_data, self.y_data):
                writer.writerow([t.strftime("%H:%M:%S"), val])
            writer.writerow(["", "", std_dev, mean, variance])
        logging.info("Data saved to .csv")
        QMessageBox.information(self, "Data Saved", f"Data saved as: {filename}")

    def button_start(self):
        self.start_time = time.time()
        self.x_data.clear()
        self.y_data.clear()

        selected_com = self.com_dropdown.currentText()
        if ": " in selected_com:
            self.com_port = selected_com.split(": ")[1]
        else:
            self.com_port = selected_com

        selected_baud = self.baud_dropdown.currentText()
        if ": " in selected_baud:
            self.baudrate = int(selected_baud.split(": ")[1])
        else:
            self.baudrate = int(selected_baud)

        self.process_start = True
        self.serial_timer.start(10)
        self.timer.start(100)
        logging.info("Starting data acquisition...")

    def button_stop(self):
        self.timer.stop()
        self.process_start = False
        logging.info("Stopping data acquisition...")

    def button_clear(self):
        self.x_data.clear()
        self.y_data.clear()
        self.init_text.set_visible(True)
        self.axes.set_visible(False) 
        self.canvas.draw()
        logging.info("Clearing plot...")

    def init_plot(self):
        controls_layout = QHBoxLayout()
        self.main_layout.addLayout(controls_layout)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        #self.canvas.move(300,300) # TODO: Remove this line
        self.canvas.setFixedSize(640,300)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_visible(False)
        self.line, = self.axes.plot([], [], lw=2)

        self.init_text = self.figure.text(
            0.5, 0.5, 
            "Data Acquisition Inactive", 
            transform=self.axes.transAxes, 
            ha='center', 
            va='center',
            fontsize=16, 
            color='gray'
        )
        self.main_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)

    def update_plot(self):
        if not self.serial_buffer:
            return

        if not getattr(self, "process_start", False):
            return
        
        if not self.axes.get_visible():
            self.axes.set_visible(True)
            self.init_text.set_visible(False)

        if not self.serial_buffer:
            return
        
        value = self.serial_buffer[-1]

        self.serial_buffer.clear()
        t_current = datetime.now(self.est_tz)
        self.x_data.append(t_current)
        self.y_data.append(value)

        while self.x_data and (t_current - self.x_data[0]).total_seconds() > 120:
            self.x_data.pop(0)
            self.y_data.pop(0)

        x_nums = mdates.date2num(self.x_data)
        self.line.set_data(x_nums, self.y_data)

        start_lim = max(self.x_data[0], t_current - timedelta(seconds=120))
        end_lim = t_current
        self.axes.set_xlim(mdates.date2num(start_lim), mdates.date2num(end_lim))
        self.axes.set_ylim(0, 100)

        formatted = mdates.DateFormatter('%I:%M:%S', tz=self.est_tz)
        self.axes.xaxis.set_major_formatter(formatted)

        for label in self.axes.get_xticklabels():
            label.set_rotation(20)
            label.set_horizontalalignment('right')
            label.set_fontsize(8)

        self.canvas.draw()

    def serial_read(self):
        if not hasattr(self, "com_port") or self.com_port is None:
            logging.info("Error: No COM Port selected")
            return None
        if not hasattr(self, "baudrate") or self.baudrate is None:
            logging.info("Error: No Baudrate selected")
            return None
        
        try:
            if not hasattr(self, "ser") or self.ser is None or not self.ser.is_open:
                self.ser = serial.Serial(self.com_port, self.baudrate, timeout=1)
                logging.info(f"Connected to {self.com_port} at {self.baudrate}")
        except serial.SerialException:
            logging.info(f"Error connecting to COM Port: {self.com_port}")
            return None

        if self.ser and self.ser.is_open:
            while self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:
                        value = float(line)
                        if 0 <= value <= 100:
                            self.serial_buffer.append(value)
                        else:
                            logging.info(f"Invalid value, out of range: {value}")
                except Exception as e:
                    logging.error(f"Error converting data: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = DataAcquisition()
    window.show() 
    app.exec_()