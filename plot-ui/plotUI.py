import re
import threading
import socket
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from hpgl_preview import HPGLPreview
from hpgl_plotter import HPGLPlotter
import time
import subprocess
import os
import platform
from tkinter import messagebox
import paramiko

def load_hpgl_file(file_path_label, dimensions_label, preview, plotter):
    # HPGL-Datei laden
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("HPGL Files", "*.hpgl")])
    if file_path:
        with open(file_path, "r") as file:
            hpgl_code = file.read()
            preview.draw(hpgl_code)  # Der Filepath wird jetzt nicht mehr übergeben
            file_path_label.config(
                text=f"Dateipfad: {file_path}"
            )  # Hier wird der file_path angezeigt
            plotter.openFile(file_path)
            w, h, l = plotter.getDimensions()
            dimensions_label.config(
                text=f"Breite {w:.1f}, Höhe {h:.1f}, Weglänge {l:.1f}"
            )


def send_hpgl_data(file_name, ip, port):
    if file_name:
        if width_checkbox_var.get():
            width = int(width_entry.get())
        else:
            width = None
        mirror = True
        plotter_ip = ip.get()
        plotter_port = int(port.get())
        plotter = HPGLPlotter(
            file_path,
            "",
            False,
            width,
            False,
            mirror,
            False,
            plotter_ip,
            plotter_port,
            gui_log,
        )
        plotter.run()


def toggle_width_entry():
    # Wenn die Checkbox aktiviert ist, das Eingabefeld aktivieren, andernfalls deaktivieren
    if width_checkbox_var.get():
        width_entry.config(state="normal")  # Aktiviert das Eingabefeld
    else:
        width_entry.delete(0, tk.END)
        width_entry.config(state="disabled")  # Deaktiviert das Eingabefeld


def validate_width_input(P):
    """Überprüft, ob die Eingabe eine gültige Zahl ist. Und updatet Vorberechnung"""
    # Erlaubt nur leere Eingabe oder eine Zahl mit optionaler Dezimalstelle
    if re.match(
        # r"^\d*\.?\d*$", P
        r"^\d+$", P
    ):  # Erlaubt nur Zahlen (optional mit Dezimalpunkt)
        # TODO: update Vorberechung der Plotgröße
        plotter.setWidth(int(P))
        plotter.configure()
        w, h, l = plotter.getDimensions()
        dimensions_label.config(
            text=f"Breite {w:.1f}, Höhe {h:.1f}, Weglänge {l:.1f}"
        )
        return True
    if P == "":
        # TODO: hier auf Originalgröße skalieren 
        plotter.prepare()
        w, h, l = plotter.getDimensions()
        dimensions_label.config(
            text=f"Breite {w:.1f}, Höhe {h:.1f}, Weglänge {l:.1f}"
        )
        return True
    return False


def gui_log(message):
    log_widget.insert("end", message + "\n")
    log_widget.see("end")


def ping_server(ip, status_label):
    """Pingt den Server zyklisch und aktualisiert das Symbol."""
    while True:
        ip_address = ip.get()
        try:
            host = socket.gethostbyname(ip_address)

            # Plattformabhängiger Parameter
            if os.name == "nt" or platform.system() == "Windows":
                param = "-n"  # Windows
            else:
                param = "-c"  # Linux/Mac

            command = ["ping", "-w", "1000", param, "1", host]

            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            try:
                # Versuch der Dekodierung mit Fehlerersatz
                output = result.stdout.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                # Fallback, falls UTF-8 nicht funktioniert
                output = result.stdout.decode("cp1252", errors="replace")

            if result.returncode == 0:
                status_label.config(text="🔵 Schneideplotter erreichbar", fg="green")
            else:
                status_label.config(
                    text="🔴 Schneideplotter nicht erreichbar", fg="red"
                )
        except Exception as e:
            status_label.config(text="🔴 Fehler beim Pingen", fg="red")

        time.sleep(2)


def shutdown_raspberry_pi(
    host,
    confirm_message="Möchten Sie den Raspberry Pi des Schneideplotters (WLAN Interface Box) wirklich herunterfahren?",
):
    """Funktion zum Herunterfahren des Raspberry Pi über SSH mit einem privaten Schlüssel."""
    confirm = messagebox.askyesno("Bestätigung", confirm_message)
    if not confirm:
        return  # Abbrechen, wenn der Benutzer "Nein" wählt

    username = "maker"  # Benutzername
    # private_key_path = "/path/to/your/private/key"  # Pfad zum privaten Schlüssel
    password = "maker"
    command = "sudo shutdown now"

    try:
        # Privaten Schlüssel laden
        # private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

        # SSH-Verbindung herstellen
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(hostname=host, username=username, pkey=private_key)
        ssh.connect(hostname=host, username=username, password=password)

        # Kommando ausführen
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Warten, bis der Befehl fertig ist

        messagebox.showinfo(
            "Erfolg", "Der Raspberry Pi des Schneideplotters wird heruntergefahren."
        )
    except Exception as e:
        messagebox.showerror("Fehler", f"Es gab ein Problem:\n{e}")
    finally:
        try:
            ssh.close()
        except Exception:
            pass  # Falls SSH-Client nicht korrekt initialisiert wurde


def on_close():
    shutdown_raspberry_pi(
        ip_entry.get(),
        "Das Programm wird geschlossen.\n\n"
        "Möchten Sie den Raspberry Pi des Schneideplotters (WLAN Interface Box) jetzt herunterfahren?",
    )
    root.destroy()


# Beispiel für die Tkinter-Anwendung
root = tk.Tk()
root.title("HPGL Vorschau")

# Die Validierung für die Eingabe aktivieren
validate_input = root.register(validate_width_input)

# Frame für das Layout erstellen
frame = tk.Frame(root)
frame.pack(side="left", padx=10, pady=10)

# Canvas für die Vorschau
canvas = tk.Canvas(frame, width=500, height=500, bg="white")
canvas.pack()

# Label für den Dateipfad
file_path_label = tk.Label(
    frame, text="Dateipfad: Noch keine Datei geladen", anchor="w"
)
file_path_label.pack(pady=10, fill="x")

file_path = None

# Button zum Laden der HPGL-Datei
load_button = tk.Button(
    frame,
    text="HPGL-Datei laden",
    command=lambda: load_hpgl_file(file_path_label, dimensions_label, preview, plotter),
)
load_button.pack(pady=10)

# Frame für Optionen
options_frame = tk.Frame(root)
options_frame.pack(side="right", padx=10, pady=10)

# Server-Status-Anzeige
status_label = tk.Label(options_frame, text="🔴 Serverstatus unbekannt", fg="red")
status_label.pack(pady=10, anchor="w")

# Eingabe für IP-Adresse
tk.Label(options_frame, text="Adresse des Schneideplotters").pack(pady=5, anchor="w")
ip_entry = tk.Entry(options_frame)
ip_entry.pack(pady=5, anchor="w")
ip_entry.insert(0, "127.0.0.1")  # Standard-IP-Adresse

# Eingabe für Port
tk.Label(options_frame, text="Port des Schneideplotter-Interface-Programms:").pack(
    pady=5, anchor="w"
)
port_entry = tk.Entry(options_frame)
port_entry.pack(pady=5, anchor="w")
port_entry.insert(0, "12345")  # Standard-Port

# Ausgabe der Dimensionen des Plots
dimensions_label = tk.Label(
    options_frame, text="Dimensionen des Plots (Breite, Höhe, Länge)", anchor="w"
)
dimensions_label.pack(pady=10, fill="x")

# Checkbox für das Überschreiben der Breite
width_checkbox_var = tk.IntVar()
width_checkbox = tk.Checkbutton(
    options_frame,
    text="Auf feste Breite skalieren (in mm)",
    variable=width_checkbox_var,
    command=toggle_width_entry,
)
width_checkbox.pack(pady=5, anchor="w")

# Eingabefeld für die Breite
width_entry = tk.Entry(
    options_frame, validate="key", validatecommand=(validate_input, "%P")
)
width_entry.pack(pady=5, fill="x", anchor="w")
width_entry.config(state="disabled")  # Standardmäßig deaktiviert

# Checkbox für Option Spiegeln
mirror_var = tk.IntVar()
mirror_checkbox = tk.Checkbutton(options_frame, text="Spiegeln", variable=mirror_var)
mirror_checkbox.pack(pady=5, anchor="w")

# Horizontale Trennlinie hinzufügen
separator = ttk.Separator(options_frame, orient="horizontal")
separator.pack(
    fill="x", pady=10
)  # `fill="x"` sorgt dafür, dass die Trennlinie die gesamte Breite einnimmt

# Button zum Senden der HPGL-Datei
send_button = tk.Button(
    options_frame,
    text="Schneidevorgang starten",
    command=lambda: send_hpgl_data(file_path, ip_entry, port_entry),
)
send_button.pack(pady=10, anchor="w")

# Button zum Herunterfahren des Schneideplotter-Raspberries
send_button = tk.Button(
    options_frame,
    text="Raspberry am Schneideplotter herunterfahren",
    command=lambda: shutdown_raspberry_pi(
        ip_entry.get(),
        "Möchten Sie den Raspberry Pi des Schneideplotters (WLAN Interface Box) jetzt herunterfahren?",
    ),
)
send_button.pack(pady=10, anchor="w")

# Textfeld für Logausgaben
log_widget = tk.Text(options_frame, wrap="word", height=10, width=50)
log_widget.pack(pady=10)

# Ereignis beim Schließen des Fensters abfangen
root.protocol("WM_DELETE_WINDOW", on_close)

# Instanziiere die HPGLPreview-Klasse
preview = HPGLPreview(canvas, file_path_label)

# Instanziiere die HPGLPlotter-Klasse
plotter = HPGLPlotter()

# Starte Pinger in eigenem Thread
threading.Thread(target=ping_server, args=(ip_entry, status_label), daemon=True).start()

# Starten der Tkinter-Anwendung
root.mainloop()
