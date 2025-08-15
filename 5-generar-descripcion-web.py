#!/usr/bin/env python

import csv
import re


def generar_pagina_web_actividades(nombre_archivo_csv, nombre_archivo_salida):
    """
    Lee un archivo CSV con datos de actividades y genera un archivo HTML con
    un diseño de mampostería usando la librería Masonry para una vista compacta.
    """

    # Encabezado del HTML, ahora incluye la referencia a Font Awesome y Masonry
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Actividades</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                color: #333;
                line-height: 1.6;
            }
            .contenedor-actividades {
                /* Contenedor principal de Masonry */
                padding: 20px;
                margin: auto;
            }
            .tarjeta-actividad {
                border: 1px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                background-color: #fff;
                margin-bottom: 20px;
                /* El ancho se define aquí para que Masonry lo use */
                width: calc(33.333% - 20px);
            }
            .tarjeta-actividad:hover {
                transform: translateY(-5px);
            }
            @media (max-width: 1200px) {
                .tarjeta-actividad {
                    width: calc(50% - 20px);
                }
            }
            @media (max-width: 768px) {
                .tarjeta-actividad {
                    width: calc(100% - 20px);
                }
            }
            .imagen-miniatura {
                width: 100%;
                height: 200px;
                object-fit: cover;
            }
            .contenido-tarjeta {
                padding: 15px;
            }
            .titulo-actividad {
                font-size: 1.25em;
                margin-top: 0;
                margin-bottom: 10px;
                color: #0056b3;
            }
            .titulo-actividad .icono-requisito {
                margin-left: 5px;
                font-size: 0.8em;
                vertical-align: middle;
            }
            .profesor {
                font-style: italic;
                color: #555;
                margin-bottom: 10px;
            }
            .descripcion-actividad {
                font-size: 0.9em;
                color: #666;
            }
            .info-adicional {
                margin-top: 15px;
                padding-top: 10px;
                border-top: 1px solid #eee;
            }
            .enlace-mas-info {
                display: inline-block;
                margin-top: 10px;
                color: #007bff;
                text-decoration: none;
                font-weight: bold;
            }
            .enlace-mas-info:hover {
                text-decoration: underline;
            }
            .materiales {
                font-size: 0.85em;
                color: #888;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Nuestras Actividades</h1>
        <div class="contenedor-actividades">
    """

    actividades_procesadas = set()

    try:
        with open(nombre_archivo_csv, encoding="utf-8") as archivo_csv:
            lector_csv = csv.DictReader(archivo_csv, delimiter=";")

            for fila in lector_csv:
                # Modificación para leer del campo EDAD y mostrar las categorías especiales
                categoria = fila.get("EDAD", "").strip().upper()
                if not fila.get("idActividad") and categoria not in [
                    "ADULTOS",
                    "AVAST",
                    "TUTORES",
                ]:
                    continue
                if not fila.get("DESCRIPCION", "").strip():
                    continue

                titulo_original = fila.get("ACTIVIDAD", "Actividad sin nombre").strip()
                titulo = re.sub(r"\s+[A-Z0-9]$", "", titulo_original).strip()

                if titulo in actividades_procesadas:
                    continue
                actividades_procesadas.add(titulo)

                profesor = fila.get("profesores", "Profesor no asignado").strip()
                descripcion = fila.get(
                    "DESCRIPCION", "Descripción no disponible"
                ).strip()
                mini_url = fila.get("MINIATURA", "").strip()
                mas_info_url = fila.get("URL", "").strip()
                materiales_texto = fila.get("MATERIALES", "").strip()

                iconos_requisitos = ""
                necesita_wifi = bool(fila.get("WIFI", "").strip())
                necesita_dispositivo = bool(fila.get("DISPOSITIVO", "").strip())

                if necesita_wifi:
                    iconos_requisitos += '<i class="fa-solid fa-wifi icono-requisito" title="Requiere Wi-Fi"></i>'
                if necesita_dispositivo:
                    iconos_requisitos += '<i class="fa-solid fa-laptop icono-requisito" title="Requiere dispositivo"></i>'

                imagen_html = ""
                if mini_url:
                    imagen_html = f'<img src="{mini_url}" alt="Miniatura de {titulo}" class="imagen-miniatura">'

                enlace_html = ""
                if mas_info_url:
                    enlace_html = f'<a href="{mas_info_url}" class="enlace-mas-info" target="_blank">Más información</a>'

                materiales_html = ""
                if materiales_texto:
                    materiales_html = (
                        f'<p class="materiales">**Materiales:** {materiales_texto}</p>'
                    )

                tarjeta_html = f"""
                <div class="tarjeta-actividad">
                    {imagen_html}
                    <div class="contenido-tarjeta">
                        <h2 class="titulo-actividad">{titulo} {iconos_requisitos}</h2>
                        <p class="profesor">Impartido por: {profesor}</p>
                        <p class="descripcion-actividad">{descripcion}</p>
                        {materiales_html}
                        <div class="info-adicional">
                            {enlace_html}
                        </div>
                    </div>
                </div>
                """
                html_content += tarjeta_html

    except FileNotFoundError:
        return "Error: El archivo CSV no fue encontrado."
    except Exception as e:
        return f"Ocurrió un error: {e}"

    # Cierre del HTML y script para inicializar Masonry
    html_content += """
        </div>
        <script src="https://unpkg.com/masonry-layout@4.2.2/dist/masonry.pkgd.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                var grid = document.querySelector('.contenedor-actividades');
                var msnry = new Masonry(grid, {
                    itemSelector: '.tarjeta-actividad',
                    columnWidth: '.tarjeta-actividad',
                    gutter: 20
                });
            });
        </script>
    </body>
    </html>
    """

    with open(nombre_archivo_salida, "w", encoding="utf-8") as archivo_salida:
        archivo_salida.write(html_content)

    return f"Página web generada con éxito en el archivo '{nombre_archivo_salida}'."


if __name__ == "__main__":
    csv_file = "actividades.csv"
    output_html_file = "pagina_actividades.html"

    resultado = generar_pagina_web_actividades(csv_file, output_html_file)
    print(resultado)
