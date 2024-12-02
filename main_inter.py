import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QFrame, QSizePolicy
from PyQt5.QtGui import QFont, QColor, QMovie, QPixmap
from PyQt5.QtCore import Qt
from interfaz_grafico import Dashboard  # Importar el Dashboard original
from interfaz_grafico_cons import DashboardVoltage  # Importar el nuevo Dashboard para voltaje
from front_noise import Dashboard as DashboardNoise  # Importar el Dashboard de Análisis de Ruido

class MenuWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Configuración inicial de la ventana
        self.setFixedSize(800, 800)  # Ajustamos la altura para acomodar el nuevo botón
        self.setWindowTitle("ATLAS Dashboard Menu")
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)

        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Layout para el logo y el título
        logo_title_layout = QVBoxLayout()
        logo_title_layout.setSpacing(10)
        logo_title_layout.setAlignment(Qt.AlignCenter)

        # Logo de ATLAS
        self.logo_label = QLabel(self)
        self.logo_label.setStyleSheet("background-color: transparent; border: none;")
        logo_pixmap = QPixmap("images/ATLAS-Logo-White-transparent.png")
        self.logo_label.setPixmap(logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setScaledContents(True)

        # Efecto de sombra en el logo
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(97, 218, 251))
        shadow.setOffset(0, 0)
        self.logo_label.setGraphicsEffect(shadow)

        # Añadir logo al layout
        logo_title_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        # Título de bienvenida
        self.welcome_label = QLabel("Welcome to the ATLAS Dashboard System", self)
        self.welcome_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("color: #61dafb;")

        # Añadir título al layout
        logo_title_layout.addWidget(self.welcome_label, alignment=Qt.AlignCenter)

        # Layout horizontal para los botones
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(30)
        self.button_layout.setAlignment(Qt.AlignCenter)

        # Marco del botón izquierdo
        left_frame = QFrame(self)
        left_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #61dafb;
                border-radius: 15px;
                background-color: #1e1e1e;
            }
        """)
        left_frame.setFixedWidth(350)
        left_button_layout = QVBoxLayout(left_frame)
        left_button_layout.setContentsMargins(10, 10, 10, 10)
        left_button_layout.setSpacing(5)

        # Añadir stretch superior para centrar verticalmente
        left_button_layout.addStretch()

        # Imagen GIF izquierda
        left_image_label = QLabel(self)
        left_image_label.setStyleSheet("background-color: transparent; border: none;")
        left_movie = QMovie("images/imagen left22.gif")
        left_movie.start()
        left_image_label.setMovie(left_movie)
        left_image_label.setAlignment(Qt.AlignCenter)
        left_image_label.setFixedSize(150, 150)

        # Añadir imagen al layout
        left_button_layout.addWidget(left_image_label, alignment=Qt.AlignCenter)

        # Botón debajo del GIF
        self.start_button_left = QPushButton("Go to Temperature Sweep Mode", self)
        self.start_button_left.setFont(QFont('Arial', 12, QFont.Bold))
        self.start_button_left.setStyleSheet(self.button_style())
        self.start_button_left.clicked.connect(self.open_dashboard)

        # Añadir botón al layout
        left_button_layout.addWidget(self.start_button_left, alignment=Qt.AlignCenter)

        # Texto descriptivo izquierdo (en negrita)
        left_text_label = QLabel(
            "<b>Temperature Sweep Mode lets you set initial and final temperatures, the number of steps, and an RMS limit. "
            "It collects and analyzes voltage and temperature data from multiple channels, determining each channel's status based on the RMS limit. "
            "Heat maps and charts make it easy to interpret the results.</b>", self)
        left_text_label.setFont(QFont('Arial', 9))
        left_text_label.setAlignment(Qt.AlignCenter)
        left_text_label.setStyleSheet("color: #dcdcdc;")
        left_text_label.setWordWrap(True)
        left_text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_text_label.setMaximumWidth(300)

        # Añadir texto al layout
        left_button_layout.addWidget(left_text_label, alignment=Qt.AlignCenter)

        # Añadir stretch inferior para centrar verticalmente
        left_button_layout.addStretch()

        # Marco del botón derecho
        right_frame = QFrame(self)
        right_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #61dafb;
                border-radius: 15px;
                background-color: #1e1e1e;
            }
        """)
        right_frame.setFixedWidth(350)
        right_button_layout = QVBoxLayout(right_frame)
        right_button_layout.setContentsMargins(10, 10, 10, 10)
        right_button_layout.setSpacing(5)

        # Añadir stretch superior para centrar verticalmente
        right_button_layout.addStretch()

        # Imagen GIF derecha
        right_image_label = QLabel(self)
        right_image_label.setStyleSheet("background-color: transparent; border: none;")
        right_movie = QMovie("images/image right.gif")
        right_movie.start()
        right_image_label.setMovie(right_movie)
        right_image_label.setAlignment(Qt.AlignCenter)
        right_image_label.setFixedSize(150, 150)

        # Añadir imagen al layout
        right_button_layout.addWidget(right_image_label, alignment=Qt.AlignCenter)

        # Botón debajo del GIF
        self.start_button_right = QPushButton("Go to Constant Voltage Mode", self)
        self.start_button_right.setFont(QFont('Arial', 12, QFont.Bold))
        self.start_button_right.setStyleSheet(self.button_style())
        self.start_button_right.clicked.connect(self.open_dashboard_voltaje)

        # Añadir botón al layout
        right_button_layout.addWidget(self.start_button_right, alignment=Qt.AlignCenter)

        # Texto descriptivo derecho (en negrita)
        right_text_label = QLabel(
            "<b>The Constant Voltage Mode allows you to set a steady voltage and specify the number of cycles, with each cycle lasting 15 seconds. "
            "This configuration enables you to conduct measurements over a consistent voltage for a defined duration, useful for observations requiring stable voltage conditions across a set period.</b>", self)
        right_text_label.setFont(QFont('Arial', 9))
        right_text_label.setAlignment(Qt.AlignCenter)
        right_text_label.setStyleSheet("color: #dcdcdc;")
        right_text_label.setWordWrap(True)
        right_text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_text_label.setMaximumWidth(300)

        # Añadir texto al layout
        right_button_layout.addWidget(right_text_label, alignment=Qt.AlignCenter)

        # Añadir stretch inferior para centrar verticalmente
        right_button_layout.addStretch()

        # Añadir marcos al layout de botones
        self.button_layout.addWidget(left_frame)
        self.button_layout.addWidget(right_frame)

        # Añadir layouts al layout principal
        self.main_layout.addStretch()
        self.main_layout.addLayout(logo_title_layout)
        self.main_layout.addLayout(self.button_layout)

        # --- Nuevo botón para el Análisis de Ruido ---
        # Marco del botón inferior
        bottom_frame = QFrame(self)
        bottom_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #61dafb;
                border-radius: 15px;
                background-color: #1e1e1e;
            }
        """)
        bottom_frame.setFixedWidth(700)  # Ancho ajustado
        bottom_button_layout = QVBoxLayout(bottom_frame)
        bottom_button_layout.setContentsMargins(10, 10, 10, 10)
        bottom_button_layout.setSpacing(5)

        # Añadir stretch superior para centrar verticalmente
        bottom_button_layout.addStretch()

        # Botón para el Análisis de Ruido
        self.start_button_bottom = QPushButton("Go to Noise Analysis Mode", self)
        self.start_button_bottom.setFont(QFont('Arial', 12, QFont.Bold))
        self.start_button_bottom.setStyleSheet(self.button_style())
        self.start_button_bottom.clicked.connect(self.open_dashboard_noise)

        # Añadir botón al layout
        bottom_button_layout.addWidget(self.start_button_bottom, alignment=Qt.AlignCenter)

        # Texto descriptivo para el Análisis de Ruido
        bottom_text_label = QLabel(
            "<b>The Noise Analysis Mode allows you to set a voltage value and analyze the noise "
            "in a DC signal. After setting the desired voltage, the oscilloscope signal is acquired "
            "and a Fast Fourier Transform (FFT) is performed to analyze the frequency spectrum. "
            "Relevant parameters such as the DC value, noise RMS voltage, and signal-to-noise ratio (SNR) "
            "are calculated. Finally, graphs of the time-domain signal and its frequency spectrum are presented.</b>", self)
        bottom_text_label.setFont(QFont('Arial', 9))
        bottom_text_label.setAlignment(Qt.AlignCenter)
        bottom_text_label.setStyleSheet("color: #dcdcdc;")
        bottom_text_label.setWordWrap(True)
        bottom_text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bottom_text_label.setMaximumWidth(700)

        # Añadir texto al layout
        bottom_button_layout.addWidget(bottom_text_label, alignment=Qt.AlignCenter)

        # Añadir stretch inferior para centrar verticalmente
        bottom_button_layout.addStretch()

        # Añadir el marco inferior al layout principal
        self.main_layout.addWidget(bottom_frame, alignment=Qt.AlignCenter)
        self.main_layout.addStretch()

    def button_style(self):
        # Estilo para los botones
        return """
            QPushButton {
                background-color: #61dafb;
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #21a1c4;
            }
            QPushButton:pressed {
                background-color: #1b8ca6;
            }
        """

    def open_dashboard(self):
        # Ocultar esta ventana y mostrar el Dashboard principal maximizado
        self.hide()
        self.dashboard = Dashboard()
        self.dashboard.showMaximized()  # Abrir el dashboard maximizado

    def open_dashboard_voltaje(self):
        # Ocultar esta ventana y mostrar el Dashboard de Voltaje maximizado
        self.hide()
        self.dashboard_voltaje = DashboardVoltage()
        self.dashboard_voltaje.showMaximized()  # Abrir el dashboard de voltaje maximizado

    def open_dashboard_noise(self):
        # Ocultar esta ventana y mostrar el Dashboard de Análisis de Ruido maximizado
        self.hide()
        self.dashboard_noise = DashboardNoise()
        self.dashboard_noise.showMaximized()  # Abrir el dashboard de ruido maximizado

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MenuWindow()
    window.show()
    sys.exit(app.exec_())
