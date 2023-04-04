#!/usr/bin/env python
import os
import time
from datetime import datetime, timedelta


def main():
    # Ruta donde se almacenan los backups
    ruta_backups = "/Ruta/donde/almacenan/backups"
    # Lista el contenido del directorio y lo almacena en una lista
    lista_archivos = os.listdir(ruta_backups)
    # Inicia las variables de tiempo hoy y fecha_limite
    hoy = datetime.now()
    fecha_limite = hoy - timedelta(days=8)

    # Recorre y elimina los archivos que hayan sido creados hace más de 8 días.
    # Como se ejecuta cada 8 días, esto permite que siempre haya 2 backups de cada VM.
    for nombre_archivo in lista_archivos:
        ruta_archivo = os.path.join(ruta_backups, nombre_archivo)
        if os.path.isfile(ruta_archivo) and nombre_archivo != 'rotar_backups.py':
            tiempo_creacion = os.path.getctime(ruta_archivo)
            tiempo_creacion_str = time.ctime(tiempo_creacion)
            fecha_creacion = datetime.strptime(tiempo_creacion_str, '%c')
            if fecha_creacion <= fecha_limite:
                os.remove(ruta_archivo)
                print(f"Eliminando el archivo: {nombre_archivo}")

    print("Se eliminaron los backups antiguos.")


if __name__ == "__main__":
    main()
