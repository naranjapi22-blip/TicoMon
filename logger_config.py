import logging
import sys

def setup_logger():
    # Crear el logger principal del bot
    logger = logging.getLogger('FumoBot')
    
    # Nivel mínimo a capturar (INFO capturará INFO, WARNING, ERROR y CRITICAL)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    # Formato de salida: Fecha - Nivel - Archivo:Línea - Mensaje
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    # Configurar el handler apuntando explícitamente a stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)

    # Añadir el handler solo si no existe para evitar logs duplicados
    if not logger.handlers:
        logger.addHandler(stdout_handler)

    return logger

# Instancia lista para importar
log = setup_logger()