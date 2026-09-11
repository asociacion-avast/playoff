#!/usr/bin/env python

import csv
import html as html_module
import re

import common


def generar_pagina_web_actividades(
    nombre_archivo_csv, nombre_archivo_salida, max_descripcion=100
):
    """
    Lee un archivo CSV con datos de actividades, filtra y agrupa por nombre de actividad y profesor,
    y genera un archivo HTML con la información formateada como tarjetas y los iconos correspondientes.

    Args:
        nombre_archivo_csv: Ruta al archivo CSV de actividades.
        nombre_archivo_salida: Ruta donde guardar el HTML generado.
        max_descripcion: Longitud máxima de la descripción en caracteres.
            Se trunca con '...' si es más larga. Por defecto 100.
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
            .info-detallada {
                margin-top: 15px;
                padding-top: 10px;
                border-top: 1px solid #eee;
                font-size: 0.85em;
                color: #555;
            }
            .info-detallada p {
                margin: 4px 0;
            }
            .info-detallada strong {
                color: #333;
            }
            .info-detallada .etiqueta {
                font-weight: bold;
                color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>Nuestras Actividades</h1>
        <div class="contenedor-actividades">
    """

    actividades_procesadas = set()

    try:
        with common.readcsv(nombre_archivo_csv, delimiter=";") as archivo_csv:
            lector_csv = csv.DictReader(archivo_csv, delimiter=";")

            for fila in lector_csv:
                # Se mantiene la lógica para mostrar categorías especiales y descripciones.
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
                profesor = fila.get("profesores", "Profesor no asignado").strip()

                unique_key = titulo
                if unique_key in actividades_procesadas:
                    continue
                actividades_procesadas.add(unique_key)

                descripcion_raw = fila.get(
                    "DESCRIPCION", "Descripción no disponible"
                ).strip()
                if len(descripcion_raw) > max_descripcion:
                    descripcion_raw = descripcion_raw[:max_descripcion] + "..."
                descripcion = html_module.escape(descripcion_raw)
                mini_url = html_module.escape(fila.get("MINIATURA", "").strip())
                mas_info_url = html_module.escape(fila.get("URL", "").strip())
                materiales_texto = html_module.escape(
                    fila.get("MATERIALES", "").strip()
                )

                iconos_requisitos = ""
                necesita_wifi = bool(fila.get("WIFI", "").strip())
                necesita_dispositivo = bool(fila.get("DISPOSITIVO", "").strip())

                if necesita_wifi:
                    iconos_requisitos += " 🛜"
                if necesita_dispositivo:
                    iconos_requisitos += " 🖥"

                imagen_html = ""
                if mini_url:
                    imagen_html = f'<img src="{mini_url}" alt="Miniatura de {html_module.escape(titulo)}" class="imagen-miniatura">'

                enlace_html = ""
                if mas_info_url:
                    enlace_html = f'<a href="{mas_info_url}" class="enlace-mas-info" target="_blank">Más información</a>'

                materiales_html = ""
                if materiales_texto:
                    materiales_html = (
                        f'<p class="materiales">**Materiales:** {materiales_texto}</p>'
                    )

                aula = html_module.escape(fila.get("AULA", "").strip())
                edificio = html_module.escape(fila.get("EDIFICIO", "").strip())
                planta = html_module.escape(fila.get("PLANTA", "").strip())
                escuela = html_module.escape(fila.get("ESCUELA", "").strip())
                clave_wifi = html_module.escape(fila.get("CLAVE WIFI", "").strip())
                dispositivo_elect = html_module.escape(
                    fila.get("DISPOSITIVO ELECT.", "").strip()
                )
                pdf_url = html_module.escape(fila.get("PDF", "").strip())

                info_detallada_items = []
                if escuela or edificio or planta or aula:
                    ubicacion_parts = []
                    if escuela:
                        ubicacion_parts.append(f"Escuela: {escuela}")
                    if edificio:
                        ubicacion_parts.append(f"Edificio: {edificio}")
                    if planta:
                        ubicacion_parts.append(f"Planta: {planta}")
                    if aula:
                        ubicacion_parts.append(f"Aula: {aula}")
                    info_detallada_items.append(
                        f"<p><span class='etiqueta'>Ubicación:</span> {', '.join(ubicacion_parts)}</p>"
                    )
                if clave_wifi and clave_wifi.upper() not in ("VERDADERO", "FALSO"):
                    info_detallada_items.append(
                        f"<p><span class='etiqueta'>Clave Wi-Fi:</span> {clave_wifi}</p>"
                    )
                if dispositivo_elect and dispositivo_elect.upper() not in (
                    "VERDADERO",
                    "FALSO",
                ):
                    info_detallada_items.append(
                        f"<p><span class='etiqueta'>Dispositivo electrónico:</span> {dispositivo_elect}</p>"
                    )

                info_detallada_html = ""
                if info_detallada_items:
                    info_detallada_html = f"""
                    <div class="info-detallada">
                        {"".join(info_detallada_items)}
                    </div>
                    """

                pdf_html = ""
                if pdf_url:
                    pdf_html = f'<p class="materiales"><a href="{pdf_url}" target="_blank" class="enlace-mas-info">PDF</a></p>'

                tarjeta_html = f"""
                <div class="tarjeta-actividad">
                    {imagen_html}
                    <div class="contenido-tarjeta">
                        <h2 class="titulo-actividad">{html_module.escape(titulo)} {iconos_requisitos}</h2>
                        <p class="profesor">Impartido por: {html_module.escape(profesor)}</p>
                        <p class="descripcion-actividad">{descripcion}</p>
                        {materiales_html}
                        {pdf_html}
                        {info_detallada_html}
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

    html_content = re.sub(r"\s+", " ", html_content)
    html_content = re.sub(r">\s+<", "><", html_content)
    html_content = html_content.strip()

    with open(nombre_archivo_salida, "w", encoding="utf-8") as archivo_salida:
        archivo_salida.write(html_content)

    return f"Página web generada con éxito en el archivo '{nombre_archivo_salida}'."


def generar_html_para_wordpress(nombre_archivo_html, nombre_archivo_salida_wordpress):
    with open(nombre_archivo_html, encoding="utf-8") as f:
        contenido_html = f.read()

    patron_estilos = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
    estilos = patron_estilos.findall(contenido_html)
    css = "\n".join(estilos)
    css = f"<style>\n{css}\n</style>" if css else ""

    contenido = re.sub(r"<!DOCTYPE[^>]*>", "", contenido_html, flags=re.IGNORECASE)
    contenido = re.sub(r"</?html[^>]*>", "", contenido, flags=re.IGNORECASE)
    contenido = re.sub(
        r"<head[^>]*>.*?</head>", "", contenido, flags=re.DOTALL | re.IGNORECASE
    )
    contenido = re.sub(r"<link[^>]*>", "", contenido, flags=re.IGNORECASE)
    contenido = re.sub(
        r"<script[^>]*>.*?</script>", "", contenido, flags=re.DOTALL | re.IGNORECASE
    )
    contenido = re.sub(r"</?body[^>]*>", "", contenido, flags=re.IGNORECASE)
    contenido = re.sub(r"^\s+|\s+$", "", contenido, flags=re.MULTILINE)
    contenido = re.sub(r"\n{3,}", "\n\n", contenido)

    contenido = re.sub(r"🛜", "[WiFi]", contenido)
    contenido = re.sub(r"🖥", "[PC]", contenido)

    contenido = re.sub(
        r'<div class="contenedor-actividades">',
        '<div class="contenedor-actividades" style="padding: 20px; margin: auto; width: 100%;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<div class="tarjeta-actividad">',
        '<div class="tarjeta-actividad" style="border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background-color: #fff; margin-bottom: 20px; display: inline-block; vertical-align: top; width: calc(33.333% - 20px); min-width: 280px;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<div class="contenido-tarjeta">',
        '<div class="contenido-tarjeta" style="padding: 15px;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<h2 class="titulo-actividad">',
        '<h2 class="titulo-actividad" style="font-size: 1.25em; margin-top: 0; margin-bottom: 10px; color: #0056b3;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<p class="profesor">',
        '<p class="profesor" style="font-style: italic; color: #555; margin-bottom: 10px;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<p class="descripcion-actividad">',
        '<p class="descripcion-actividad" style="font-size: 0.9em; color: #666;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<div class="info-adicional">',
        '<div class="info-adicional" style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<a href="([^"]*)" class="enlace-mas-info" target="_blank">',
        r'<a href="\1" class="enlace-mas-info" target="_blank" style="display: inline-block; margin-top: 10px; color: #007bff; text-decoration: none; font-weight: bold;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido = re.sub(
        r'<img src="([^"]*)" alt="[^"]*" class="imagen-miniatura">',
        r'<img src="\1" class="imagen-miniatura" style="width: 100%; height: 200px; object-fit: cover;">',
        contenido,
        flags=re.IGNORECASE,
    )

    contenido_final = css + "\n" + contenido

    with open(nombre_archivo_salida_wordpress, "w", encoding="utf-8") as archivo_salida:
        archivo_salida.write(contenido_final)

    return f"HTML para WordPress generado en '{nombre_archivo_salida_wordpress}'."


if __name__ == "__main__":
    csv_file = "actividades.csv"
    output_html_file = "pagina_actividades.html"
    output_wp_file = "pagina_actividades-wordpress.html"

    resultado = generar_pagina_web_actividades(csv_file, output_html_file)
    print(resultado)

    resultado_wp = generar_html_para_wordpress(output_html_file, output_wp_file)
    print(resultado_wp)
