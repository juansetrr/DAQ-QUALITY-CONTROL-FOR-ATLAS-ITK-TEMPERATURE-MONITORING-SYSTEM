import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QMessageBox, QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import os
import pickle

class WorkerThread(QThread):
    finished = pyqtSignal()

    def __init__(self, voltage):
        super().__init__()
        self.voltage = voltage

    def run(self):
        # Ejecutar el código de adquisición de datos con el voltaje especificado
        subprocess.call(["python", "noise_analisis.py", str(self.voltage)])
        self.finished.emit()

class GraphWidget(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Crear la figura y el canvas
        self.figure = plt.Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.figure)

        # Personalizar el fondo de la figura y los ejes
        self.figure.patch.set_facecolor('#1e1e1e')  # Fondo oscuro para la figura
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')  # Fondo oscuro para los ejes
        self.ax.tick_params(colors='white')  # Color blanco para los números de los ejes
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('#61dafb')  # Azul claro para el título

        # Agregar la barra de navegación
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: #0079c2; color: white;")  # Fondo azul y texto blanco

        # Agregar el canvas y la barra de navegación al layout
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

    def get_ax(self):
        # Devolver el objeto de ejes
        return self.ax

    def draw(self):
        # Redibujar el canvas
        self.canvas.draw()

    def clear(self):
        # Limpiar los ejes
        self.ax.clear()

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        # Crear un QScrollArea
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)

        # Establecer tema oscuro
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.setWindowTitle("Análisis de Ruido - ATLAS")
        self.setGeometry(100, 100, 1000, 700)

        # Usar una fuente moderna
        self.setFont(QFont('Arial', 10))

        # ----- Barra Superior -----
        header_frame = QFrame(self)
        header_frame.setStyleSheet("background-color: #0079c2;")
        header_frame.setFixedHeight(130)

        # Logo de ATLAS alineado a la izquierda
        atlas_label = QLabel(header_frame)
        atlas_pixmap = QPixmap("images/ATLAS-Logo-White-transparent.png")  # Ajusta la ruta de tu imagen
        atlas_pixmap = atlas_pixmap.scaled(200, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        atlas_label.setPixmap(atlas_pixmap)
        atlas_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Botón "Return to Menu" alineado a la derecha
        self.return_button = QPushButton("Return to Menu", header_frame)
        self.return_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.return_button.setStyleSheet(self.button_style())
        self.return_button.clicked.connect(self.return_to_menu)
        self.return_button.setFixedSize(150, 40)  # Ajustar tamaño del botón

        # Layout horizontal para la barra superior
        header_layout = QHBoxLayout(header_frame)
        header_layout.addWidget(atlas_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(self.return_button, alignment=Qt.AlignRight)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # ----- Sección de Introducción -----
        intro_frame = QFrame(self)
        intro_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        # Texto de introducción dentro del marco usando QLabel
        intro_label = QLabel(intro_frame)
        intro_label.setTextFormat(Qt.RichText)
        intro_label.setWordWrap(True)
        intro_label.setText(
            "<div style='text-align: justify;'>"
            "This program allows you to set the voltage value of a power supply and analyze noise "
            "in a DC signal. After setting the desired voltage, the signal is acquired from the oscilloscope "
            "and a Fast Fourier Transform (FFT) is performed to analyze the frequency spectrum. "
            "Relevant parameters such as the DC value, the RMS voltage of the noise, and the Signal-to-Noise Ratio (SNR) are calculated. "
            "Finally, graphs of the signal in the time domain and its frequency spectrum are presented."
            "</div>"
        )

        intro_label.setFont(QFont('Arial', 14))
        intro_label.setAlignment(Qt.AlignCenter)
        intro_label.setStyleSheet("color: #ffffff;")

        # Layout vertical para el texto de introducción dentro del marco
        intro_layout = QVBoxLayout(intro_frame)
        intro_layout.addWidget(intro_label)

        # ----- Sección de Parámetros -----
        parametros_frame = QFrame(self)
        parametros_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
            }
        """)

        parametros_label = QLabel("Parameters", parametros_frame)
        parametros_label.setFont(QFont('Arial', 16, QFont.Bold))
        parametros_label.setAlignment(Qt.AlignCenter)
        parametros_label.setStyleSheet("color: #61dafb;")

        # Entrada para el valor de voltaje
        self.voltage_input = QLineEdit(parametros_frame)
        self.voltage_input.setPlaceholderText("Enter the voltage value (V)")
        self.voltage_input.setStyleSheet(self.input_style())

        # Botón para iniciar el proceso
        self.start_button = QPushButton('Start Process', parametros_frame)
        self.start_button.clicked.connect(self.iniciar_proceso)
        self.start_button.setFont(QFont('Arial', 12, QFont.Bold))
        self.start_button.setStyleSheet(self.button_style())

        # Etiqueta para mostrar mensajes al usuario
        self.status_label = QLabel('', parametros_frame)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #f44747;")
        self.status_label.setFont(QFont('Arial', 12))

        # Layout para los parámetros
        parametros_layout = QVBoxLayout(parametros_frame)
        parametros_layout.addWidget(parametros_label)
        parametros_layout.addWidget(self.voltage_input)
        parametros_layout.addWidget(self.start_button)
        parametros_layout.addWidget(self.status_label)
        parametros_layout.setContentsMargins(20, 20, 20, 20)

        # ----- Sección de Resultados -----
        self.results_frame = QFrame(self)
        self.results_frame.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        self.results_frame.setVisible(False)  # Inicialmente oculto

        # Etiquetas para mostrar los resultados
        self.dc_label = QLabel('', self.results_frame)
        self.noise_rms_label = QLabel('', self.results_frame)
        self.snr_label = QLabel('', self.results_frame)

        self.dc_label.setFont(QFont('Arial', 12))
        self.noise_rms_label.setFont(QFont('Arial', 12))
        self.snr_label.setFont(QFont('Arial', 12))

        self.dc_label.setStyleSheet("color: #ffffff;")
        self.noise_rms_label.setStyleSheet("color: #ffffff;")
        self.snr_label.setStyleSheet("color: #ffffff;")

        # Layout para los resultados
        results_layout = QVBoxLayout(self.results_frame)
        results_layout.addWidget(self.dc_label)
        results_layout.addWidget(self.noise_rms_label)
        results_layout.addWidget(self.snr_label)
        results_layout.setContentsMargins(20, 20, 20, 20)

        # ----- Gráficas -----
        self.graph_widget_signal = GraphWidget(self, width=10, height=4, dpi=100)
        self.graph_widget_fft = GraphWidget(self, width=10, height=4, dpi=100)

        self.graph_widget_signal.setVisible(False)
        self.graph_widget_fft.setVisible(False)

        # Layout principal vertical
        vbox_main = QVBoxLayout(scroll_content)
        vbox_main.setAlignment(Qt.AlignTop)
        vbox_main.addWidget(header_frame)
        vbox_main.addWidget(intro_frame)
        vbox_main.addWidget(parametros_frame)
        vbox_main.addWidget(self.results_frame)
        vbox_main.addWidget(self.graph_widget_signal)
        vbox_main.addWidget(self.graph_widget_fft)
        vbox_main.setSpacing(20)
        vbox_main.setContentsMargins(20, 20, 20, 20)

        # Layout principal para toda la ventana
        layout_principal = QVBoxLayout(self)
        layout_principal.addWidget(scroll_area)

    def return_to_menu(self):
        self.close()
        from main_inter import MenuWindow  # Importar aquí para evitar importaciones circulares
        self.menu_window = MenuWindow()
        self.menu_window.show()

    def iniciar_proceso(self):
        # Obtener el valor de voltaje
        try:
            voltage = float(self.voltage_input.text())
            self.status_label.setText("Processing...")
            self.start_button.setEnabled(False)

            # Iniciar el hilo de trabajo
            self.worker = WorkerThread(voltage)
            self.worker.finished.connect(self.proceso_terminado)
            self.worker.start()
        except ValueError:
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid voltage value.')

    def proceso_terminado(self):
        self.start_button.setEnabled(True)
        self.status_label.setText("Proceso completado.")
        # Cargar datos desde datos.pkl
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            datos_path = os.path.join(script_dir, 'datosfft3.pkl')
            with open(datos_path, 'rb') as f:
                data = pickle.load(f)

            voltajes = data['voltajes']
            tiempos = data['tiempos']
            fft_freqs = data['fft_freqs']
            fft_magnitude = data['fft_magnitude']
            dc_value = data['dc_value']
            noise_rms = data['noise_rms']
            snr = data['snr']

            self.dc_label.setText(f"DC Value: {dc_value:.6f} V")
            self.noise_rms_label.setText(f"Noise RMS Voltage: {noise_rms:.6f} V")
            self.snr_label.setText(f"SNR: {snr:.2f} dB")

             # Show the results section and graphs
            self.results_frame.setVisible(True)
            self.graph_widget_signal.setVisible(True)
            self.graph_widget_fft.setVisible(True)

            # Plot signal in the time domain
            self.graph_widget_signal.clear()
            ax_signal = self.graph_widget_signal.get_ax()
            ax_signal.plot(tiempos, voltajes, color='#61dafb')
            ax_signal.set_title("Signal in Time Domain", color='#61dafb')
            ax_signal.set_xlabel("Time (s)", color='#61dafb')
            ax_signal.set_ylabel("Voltage (V)", color='#61dafb')
            ax_signal.tick_params(colors='#ffffff')
            for spine in ax_signal.spines.values():
                spine.set_color('#ffffff')
            self.graph_widget_signal.draw()

           
            # Plot frequency spectrum (FFT)
            self.graph_widget_fft.clear()
            ax_fft = self.graph_widget_fft.get_ax()
            ax_fft.plot(fft_freqs, fft_magnitude, color='#61dafb')
            ax_fft.set_title("Frequency Spectrum (FFT)", color='#61dafb')
            ax_fft.set_xlabel("Frequency (Hz)", color='#61dafb')
            ax_fft.set_ylabel("Amplitude (V)", color='#61dafb')

            ax_fft.tick_params(colors='#ffffff')
            for spine in ax_fft.spines.values():
                spine.set_color('#ffffff')
            self.graph_widget_fft.draw()

        except Exception as e:
            QMessageBox.critical(self, 'Error', f"No se pudo cargar los datos: {e}")

    def input_style(self):
        return """
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #5c5c5c;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #61dafb;
            }
        """

    def button_style(self):
        return """
            QPushButton {
                background-color: #61dafb;
                border: none;
                border-radius: 5px;
                padding: 10px;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #21a1c4;
            }
            QPushButton:pressed {
                background-color: #1b8ca6;
            }
            QPushButton:disabled {
                background-color: #3c3f41;
                color: #5c5c5c;
            }
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.showMaximized()
    sys.exit(app.exec_())
