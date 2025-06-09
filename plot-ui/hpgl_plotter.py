import sys
import socket
from hpgl import HPGL
try:
    import serial
except ImportError:
    raise ImportError("You need to install pyserial. "
                      "On Debian/Ubuntu try "
                      "sudo apt-get install python-serial")


class HPGLPlotter:
    def __init__(self, file=None, port="/dev/ttyUSB0", magic=False, width=None, preview=False,
                 mirror=False, pen=False, tcp_host=None, tcp_port=None, 
                 log_callback=None):
        """
        Initialisiert den Plotter mit expliziten Argumenten.

        :param file: Pfad zur HPGL-Datei
        :param port: Serieller Port (Standard: /dev/ttyUSB0)
        :param magic: Aktiviert automatische Optimierungen
        :param width: Skaliert die Breite auf einen angegebenen Wert in mm
        :param preview: Zeigt eine Vorschau an, bevor geplottet wird
        :param mirror: Spiegelt die Achse für invertierte Schnitte
        :param pen: Deaktiviert Schnittoptimierung für drehende Messer
        :param tcp_host: Hostname oder IP-Adresse für TCP-Streaming
        :param tcp_port: Port für TCP-Streaming
        :param log_callback: Callback-Funktion für Ausgaben (z. B. GUI-Logging)
        """
        self.file = file
        self.port = port
        self.magic = magic
        self.width = width
        self.preview = preview
        self.mirror = not mirror  # Standardmäßig spiegeln
        self.pen = pen
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.hpgl_input = None
        self.blade_optimize = False
        self.optimize = False
        self.reroute = False
        self.rotate180 = False
        self.margin = 5
        self.log_callback = log_callback or print

    def log(self, message):
        """Schreibt eine Nachricht über die Log-Callback-Funktion."""
        if self.log_callback:
            self.log_callback(message)

    def load_hpgl_file(self):
        """Lädt die HPGL-Datei und initialisiert das HPGL-Objekt."""
        try:
            self.hpgl_input = HPGL(self.file)
        except Exception as e:
            self.log("No/wrong/empty file given in argument.")
            raise e

    def configure(self):
        """Konfiguriert die Optimierungs- und Skalierungseinstellungen basierend auf den Attributen."""
        if self.magic:
            self.blade_optimize = True
            self.reroute = True
            self.optimize = True
            self.rotate180 = True

        if self.width is not None:
            self.hpgl_input.scaleToWidth(self.width)

        if self.pen:
            self.blade_optimize = False

        if self.rotate180:
            self.hpgl_input.mirrorX()
            self.hpgl_input.mirrorY()

        if self.mirror:
            self.hpgl_input.mirrorX()

        if self.optimize:
            self.hpgl_input.optimize()
            self.hpgl_input.fit()

        if self.blade_optimize:
            self.hpgl_input.optimizeCut(0.25)
            self.hpgl_input.bladeOffset(0.25)

        if self.reroute:
            self.hpgl_input.rerouteXY()

    def send_over_serial(self):
        """Sendet die HPGL-Daten über die serielle Schnittstelle."""
        self.log(f"Using serial port: {self.port}")
        hpgl_data = self.hpgl_input.getHPGL()
        self.log(f"{len(hpgl_data)} characters loaded")

        try:
            port = serial.Serial(
                port=self.port,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                rtscts=True,
                dsrdtr=True
            )

            commands = hpgl_data.split(";")
            total = len(commands)

            self.log("Starting...")
            for i, command in enumerate(commands):
                self.log(f"Sending... {((i + 1) * 100.0 / total):.1f}% done ({i + 1}/{total})")
                if command:  # Ignoriere leere Befehle
                    port.write(command.encode() + b";")
            port.write("PU0,0;SP0;SP0;")
            self.log("Serial communication finished.")
        except serial.serialutil.SerialException:
            self.log(f"Failed to open serial port {self.port}.")

    def send_over_tcp(self):
        """Sendet die HPGL-Daten als TCP-Stream an den angegebenen Host und Port."""
        if not self.tcp_host or not self.tcp_port:
            self.log("TCP host and port must be specified for TCP streaming.")
            return

        self.log(f"Sending data over TCP to {self.tcp_host}:{self.tcp_port}")
        hpgl_data = self.hpgl_input.getHPGL()
        self.log(f"{len(hpgl_data)} characters loaded")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.tcp_host, self.tcp_port))
                # s.sendall(hpgl_data.encode())

                commands = hpgl_data.split(";")
                total = len(commands)
                self.log("Starting...")
                for i, command in enumerate(commands):
                    self.log(f"Sending... {((i + 1) * 100.0 / total):.1f}% done ({i + 1}/{total})")
                    if command:  # Ignoriere leere Befehle
                        s.sendall((command + ";").encode())
                        s.sendall("PU0,0;SP0;SP0;".encode())
                self.log("Data successfully sent over TCP.")
        except Exception as e:
            self.log(f"Failed to send data over TCP: {e}")

    def getDimensions(self):
        w, h = self.hpgl_input.getSize()
        movement = sum(self.hpgl_input.getLength())
        return w, h, movement
    
    def setMirror(self, mirror):
        self.mirror = mirror
        
    def setWidth(self, width):
        self.width = width

    def openFile(self, file):
        self.file = file
        self.prepare()

    def prepare(self):
        """Führt alle vorbereitenden Schritte aus: Laden, Konfigurieren"""
        self.load_hpgl_file()
        w, h = self.hpgl_input.getSize()
        self.log("Plotting file: " + self.file)
        self.log(f"Plotting area is {w / 10:.1f}cm x {h / 10:.1f}cm")
        self.log(f" -> Total area: {w / 10 * h / 10:.1f} cm^2")
        movement = sum(self.hpgl_input.getLength())
        self.log(f" -> Total movement: {movement / 10:.1f} cm")

    def send(self):
        """Sendet die Daten"""
    
        if self.tcp_host and self.tcp_port:
            self.send_over_tcp()
        else:
            self.send_over_serial()

    def run(self):
        """Führt alle Schritte aus: Laden, Konfigurieren und Plotten."""
        self.prepare()
        self.send()
        
