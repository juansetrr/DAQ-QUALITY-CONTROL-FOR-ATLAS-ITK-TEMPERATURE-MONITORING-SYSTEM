import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer
from main_inter import MenuWindow  # Importa la clase MenuWindow desde main_inter.py

class LoadingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Cargar la animación GIF para la animación de bienvenida principal
        loading_movie = QMovie("images/imagen_loading.gif")  # Asegúrate de que el archivo GIF tiene la extensión correcta
        loading_movie.start()

        # Configuración inicial de la ventana de bienvenida para hacerla compacta
        self.setFixedSize(400, 300)  # Tamaño compacto para la pantalla de bienvenida (pantalla de carga)
        self.setWindowTitle("Welcome - ATLAS")
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)  # Deshabilitar el botón de maximizar

        # Diseño principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes para evitar el rectángulo gris
        self.main_layout.setSpacing(0)  # Sin espacio adicional

        # Animación de bienvenida
        self.welcome_animation_label = QLabel(self)
        self.welcome_animation_label.setAlignment(Qt.AlignCenter)
        self.welcome_animation_label.setStyleSheet("background-color: transparent;")  # Fondo transparente
        self.welcome_animation_label.setMovie(loading_movie)
        self.main_layout.addWidget(self.welcome_animation_label)

        # Barra de progreso de carga
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 0px;
                text-align: center;
                color: #ffffff;
                background-color: #1e1e1e;  /* Fondo consistente con el fondo de la ventana */
            }
            QProgressBar::chunk {
                background-color: #61dafb;
            }
        """)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(30)  # Altura fija para la barra de progreso
        self.main_layout.addWidget(self.progress_bar)

        # Iniciar la simulación de carga
        self.simulate_loading()

    def simulate_loading(self):
        # Simular el progreso de la barra de carga
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress_bar)
        self.timer.start(50)  # Actualizar cada 50 ms

    def update_progress_bar(self):
        value = self.progress_bar.value() + 1  # Incrementar en 1 en lugar de 2
        if value >= 100:
            self.progress_bar.setValue(100)  # Asegurar que la barra llegue al 100%
            self.timer.stop()
            self.launch_menu()
        else:
            self.progress_bar.setValue(value)

    def launch_menu(self):
        # Cerrar esta ventana y lanzar la ventana del menú
        self.close()
        self.menu_window = MenuWindow()
        self.menu_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoadingWindow()
    window.show()
    sys.exit(app.exec_())
