#!/usr/bin/env python

import argparse
import os
from datetime import datetime

import numpy as np
import pandas as pd

# Definición de los colores según el rango de edad
# Se han añadido colores para los nuevos grupos: 'TUTORES' y 'ADULTOS AVAST'
COLORES = {
    (2017, 2020): "#FCF37C",
    (2014, 2016): "#FCBB8B",
    (2011, 2013): "#81D3C9",
    (2003, 2010): "#EFC1FD",
    ("TUTORES", "TUTORES"): "#87CEEB",
    ("ADULTOS AVAST", "ADULTOS AVAST"): "#D3D3D3",
}

# Colores de la paleta del logotipo
COLOR_AZUL_OSCURO = "#00546e"
COLOR_CIAN_BRILLANTE = "#00bac3"
COLOR_UBICACION_FONDO = "#9cc9d6"


def generar_html_tabla(df, horarios_fijos, anio_nacimiento, anio_academico):
    """
    Genera el HTML de la tabla de horario a partir de un DataFrame procesado.
    """
    html_output = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Horario de Actividades</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{ font-family: sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: center; vertical-align: middle; }}
            th {{ background-color: {COLOR_AZUL_OSCURO}; color: white; }}
            .location-cell {{ font-weight: bold; background-color: {COLOR_UBICACION_FONDO}; color: {COLOR_AZUL_OSCURO}; padding: 10px; white-space: nowrap; }}
            .actividad-cell {{ word-wrap: break-word; }}
            .actividad-cell span {{ white-space: nowrap; }}
            .location-header {{ font-size: 0.9em; font-weight: normal; }}
            .anio-header {{ font-size: 1.5em; text-align: center; margin-bottom: 20px; }}
            .academic-year-header {{ font-size: 1.8em; font-weight: bold; text-align: center; margin-bottom: 10px; color: {COLOR_AZUL_OSCURO}; }}
            /* Estilo para los rangos de edad para que el texto sea legible sobre el fondo */
            .actividad-cell span[style*="background-color"] {{
                color: black !important;
            }}
        </style>
    </head>
    <body>
    """
    html_output += f"<div class='academic-year-header'>Horario de Actividades Curso Académico {anio_academico}</div>"
    if anio_nacimiento and not isinstance(anio_nacimiento, str):
        html_output += (
            f"<div class='anio-header'>Para nacidos en {anio_nacimiento}</div>"
        )
    elif isinstance(anio_nacimiento, str):
        html_output += f"<div class='anio-header'>Para el grupo {anio_nacimiento}</div>"

    html_output += """
    <table>
    <thead>
        <tr>
            <th colspan='4'>UBICACIÓN</th>
            """
    for header in horarios_fijos.keys():
        html_output += f"<th>{header}</th>"
    html_output += """
        </tr>
        <tr>
            <th class='location-header'>Escuela</th>
            <th class='location-header'>Edificio</th>
            <th class='location-header'>Planta</th>
            <th class='location-header'>Aula</th>
        """
    for _ in horarios_fijos.keys():
        html_output += "<th></th>"
    html_output += """
        </tr>
    </thead>
    <tbody>
    """

    last_escuela = None
    last_edificio = None

    for index, row in df.iterrows():
        html_output += "<tr>"

        # Celdas con rowspan para ESCUELA y EDIFICIO
        if row["ESCUELA"] != last_escuela:
            html_output += f"<td class='location-cell' rowspan='{row['rowspan_escuela']}'><a href='https://asociacion-avast.org/ubicacion/' target='_blank' style='color: {COLOR_AZUL_OSCURO}; text-decoration: none;'>{row['ESCUELA']}</a></td>"
            last_escuela = row["ESCUELA"]

        if row["EDIFICIO"] != last_edificio:
            html_output += f"<td class='location-cell' rowspan='{row['rowspan_edificio']}'>{row['EDIFICIO']}</td>"
            last_edificio = row["EDIFICIO"]

        html_output += f"<td class='location-cell'>{row['PLANTA']}</td>"
        html_output += f"<td class='location-cell'>{row['AULA']}</td>"

        # Celdas de horario
        for col in horarios_fijos.keys():
            html_output += f"<td class='actividad-cell'>{row[col]}</td>"

        html_output += "</tr>"

    html_output += """
    </tbody>
    </table>
    </body>
    </html>
    """
    return html_output


def generar_horario_para_anio(df, anio_nacimiento, horarios_fijos, anio_academico):
    """
    Genera una tabla de horario en formato HTML para un año de nacimiento específico.
    """
    # Se filtra por año de nacimiento O por los nuevos grupos (TUTORES, ADULTOS AVAST)
    if isinstance(anio_nacimiento, str):
        # Lógica para filtrar solo por el grupo de edad string (ej. 'TUTORES' o 'ADULTOS AVAST')
        df_filtrado = df[
            (df["AÑO INICIO"] == anio_nacimiento) | (df["AÑO FIN"] == anio_nacimiento)
        ].copy()
    else:
        # Lógica para filtrar por un año de nacimiento numérico, incluyendo siempre TUTORES
        df_filtrado = df[
            (
                (pd.to_numeric(df["AÑO INICIO"], errors="coerce") <= anio_nacimiento)
                & (pd.to_numeric(df["AÑO FIN"], errors="coerce") >= anio_nacimiento)
            )
            | (df["AÑO INICIO"] == "TUTORES")
        ].copy()

    if df_filtrado.empty:
        print(f"❌ No se encontraron actividades para el grupo: {anio_nacimiento}")
        return None, None

    locations = df_filtrado[["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]].drop_duplicates()
    final_schedule = pd.DataFrame(
        index=locations.index,
        columns=["ESCUELA", "EDIFICIO", "PLANTA", "AULA"] + list(horarios_fijos.keys()),
    )
    final_schedule[["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]] = locations
    final_schedule = final_schedule.sort_values(
        by=["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]
    )
    final_schedule = final_schedule.set_index(["ESCUELA", "EDIFICIO", "PLANTA", "AULA"])
    final_schedule = final_schedule.fillna("")

    for index, row in df_filtrado.iterrows():
        loc_tuple = (row["ESCUELA"], row["EDIFICIO"], row["PLANTA"], row["AULA"])

        anos_inicio_act = row["AÑO INICIO"]
        anos_fin_act = row["AÑO FIN"]

        rangos_ajustados_html = []

        # Lógica para mostrar las etiquetas de edad o de grupo (TUTORES, ADULTOS)
        for rango, color in COLORES.items():
            rango_inicio_def = rango[0]
            rango_fin_def = rango[1]

            if isinstance(rango_inicio_def, int):
                # Lógica para rangos de edad numéricos
                try:
                    overlap_start = max(rango_inicio_def, int(anos_inicio_act))
                    overlap_end = min(rango_fin_def, int(anos_fin_act))
                    if overlap_start <= overlap_end:
                        rangos_ajustados_html.append(
                            f"<span style='background-color: {color}; color: black; padding: 2px 4px; border-radius: 4px; font-weight: bold; margin-right: 2px;'>{overlap_start}-{overlap_end}</span>"
                        )
                except ValueError:
                    continue  # Si no son números, pasamos al siguiente rango
            else:
                # Lógica para rangos de texto (TUTORES, ADULTOS AVAST)
                if anos_inicio_act == rango_inicio_def:
                    rangos_ajustados_html.append(
                        f"<span style='background-color: {color}; color: white; padding: 2px 4px; border-radius: 4px; font-weight: bold; margin-right: 2px;'>{rango_inicio_def}</span>"
                    )

        iconos_html = ""
        if row.get("WIFI", ""):
            iconos_html += f"<i class='fa-solid fa-wifi' style='color: {COLOR_AZUL_OSCURO};' title='Requiere clave Wifi'></i>&nbsp;"
        if row.get("DISPOSITIVO", ""):
            iconos_html += f"<i class='fa-solid fa-mobile-screen' style='color: {COLOR_AZUL_OSCURO};' title='Requiere dispositivo del socio'></i>&nbsp;"

        etiquetas_html = ""
        if iconos_html or rangos_ajustados_html:
            etiquetas_html = "<br>" + iconos_html + "".join(rangos_ajustados_html)

        profesor_html = ""
        if row["profesores"]:
            profesor_html = (
                f"<span style='font-size: small;'>{row['profesores']}</span><br>"
            )

        descripcion_html = ""
        if row["DESCRIPCION"]:
            descripcion_html = f"title='{row['DESCRIPCION']}'"

        # Reemplazar saltos de línea del CSV con <br> para HTML
        actividad_con_saltos = row["ACTIVIDAD"].replace("\n", "<br>").replace("\r", "")

        contenido_actividad = f"{profesor_html}<b {descripcion_html}>{actividad_con_saltos}</b>{etiquetas_html}"

        hora_inicio_act = datetime.strptime(row["HORA_INICIO_STR"], "%H:%M")
        hora_fin_act = datetime.strptime(row["HORA_FIN_STR"], "%H:%M")

        for col_name, (start_str, end_str) in horarios_fijos.items():
            hora_inicio_col = datetime.strptime(start_str, "%H:%M")
            hora_fin_col = datetime.strptime(end_str, "%H:%M")

            if col_name == "11:05 - 11:30":
                final_schedule.loc[loc_tuple, col_name] = "Descanso"
                continue

            if hora_inicio_act >= hora_inicio_col and hora_inicio_act < hora_fin_col:
                if hora_fin_act <= hora_fin_col:
                    final_schedule.loc[loc_tuple, col_name] = contenido_actividad
                else:
                    final_schedule.loc[loc_tuple, col_name] = contenido_actividad
                    horarios_list = list(horarios_fijos.keys())
                    current_col_index = horarios_list.index(col_name)
                    for next_col_name in horarios_list[current_col_index + 1 :]:
                        next_start_str, next_end_str = horarios_fijos[next_col_name]
                        next_hora_inicio_col = datetime.strptime(
                            next_start_str, "%H:%M"
                        )
                        if hora_fin_act > next_hora_inicio_col:
                            final_schedule.loc[loc_tuple, next_col_name] = (
                                f"<b>{row['ACTIVIDAD']}</b> <br> continuación"
                            )
                            if hora_fin_act <= datetime.strptime(next_end_str, "%H:%M"):
                                break

    final_schedule = final_schedule.reset_index()

    # Calcular rowspan para ESCUELA y EDIFICIO
    final_schedule["rowspan_escuela"] = final_schedule.groupby("ESCUELA")[
        "ESCUELA"
    ].transform("count")
    final_schedule["rowspan_edificio"] = final_schedule.groupby(
        ["ESCUELA", "EDIFICIO"]
    )["EDIFICIO"].transform("count")

    # Eliminar filas duplicadas para las celdas con rowspan
    df_with_rowspan = final_schedule.copy()

    html_output = generar_html_tabla(
        df_with_rowspan, horarios_fijos, anio_nacimiento, anio_academico
    )
    output_filename = f"horario_filtrado-{anio_nacimiento}.html"
    return html_output, output_filename


def generar_horario_final(csv_path, anio_nacimiento=None, anio_fin=None):
    """
    Lee un CSV de actividades y genera una tabla de horario en HTML.
    Puede generar un solo horario o un rango de ellos.
    """
    try:
        # Lógica para determinar el año académico en curso (del 1 de julio al 30 de junio)
        hoy = datetime.now()
        anio_actual = hoy.year
        if hoy.month >= 7:
            anio_academico = f"{anio_actual}-{anio_actual + 1}"
        else:
            anio_academico = f"{anio_actual - 1}-{anio_actual}"

        required_cols = [
            "ACTIVIDAD",
            "HORA",
            "AULA",
            "EDIFICIO",
            "PLANTA",
            "ESCUELA",
            "AÑO INICIO",
            "AÑO FIN",
            "profesores",
            "WIFI",
            "DISPOSITIVO",
            "DESCRIPCION",
            "MATERIALES",
        ]

        # Eliminamos el reemplazo de saltos de línea al leer el CSV para mantenerlos
        df = pd.read_csv(
            csv_path, delimiter=";", encoding="utf-8", keep_default_na=False
        )

        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            print(
                f"❌ Error: El archivo CSV no contiene las siguientes columnas requeridas: {', '.join(missing_cols)}"
            )
            return

        for col in required_cols:
            df[col] = df[col].replace(np.nan, "", regex=True)

        for col in [
            "HORA",
            "AULA",
            "EDIFICIO",
            "ESCUELA",
            "profesores",
            "WIFI",
            "DISPOSITIVO",
            "DESCRIPCION",
            "MATERIALES",
        ]:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("\n", " ")
                .str.replace("\r", " ")
                .str.strip()
            )

        # Mantenemos los saltos de línea en la columna ACTIVIDAD
        df["ACTIVIDAD"] = df["ACTIVIDAD"].astype(str)

        df["PLANTA"] = (
            pd.to_numeric(df["PLANTA"], errors="coerce").fillna(0).astype(int)
        )

        # Se convierte a string para manejar los nuevos valores de texto
        df["AÑO INICIO"] = df["AÑO INICIO"].astype(str)
        df["AÑO FIN"] = df["AÑO FIN"].astype(str)

        df["HORA_INICIO_STR"] = (
            df["HORA"].str.split("-").str[0].str.strip().replace("", "00:00")
        )
        df["HORA_FIN_STR"] = (
            df["HORA"].str.split("-").str[1].str.strip().replace("", "00:00")
        )

        df["DURACION_MINS"] = (
            pd.to_datetime(df["HORA_FIN_STR"], format="%H:%M", errors="coerce")
            - pd.to_datetime(df["HORA_INICIO_STR"], format="%H:%M", errors="coerce")
        ).dt.total_seconds() / 60

        df = df.dropna(subset=["DURACION_MINS"])

        horarios_fijos = {
            "9:00 - 10:00": ("09:00", "10:00"),
            "10:05 - 11:05": ("10:05", "11:05"),
            "11:05 - 11:30": ("11:05", "11:30"),
            "11:30 - 12:30": ("11:30", "12:30"),
            "12:35 - 13:35": ("12:35", "13:35"),
        }

        if anio_nacimiento is None:
            print("Generando horario completo...")

            # Al generar el horario completo, se incluyen todas las actividades
            df_a_procesar = df

            locations = df_a_procesar[
                ["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]
            ].drop_duplicates()
            final_schedule = pd.DataFrame(
                index=locations.index,
                columns=["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]
                + list(horarios_fijos.keys()),
            )
            final_schedule[["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]] = locations
            final_schedule = final_schedule.sort_values(
                by=["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]
            )
            final_schedule = final_schedule.set_index(
                ["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]
            )
            final_schedule = final_schedule.fillna("")
            for index, row in df_a_procesar.iterrows():
                loc_tuple = (
                    row["ESCUELA"],
                    row["EDIFICIO"],
                    row["PLANTA"],
                    row["AULA"],
                )

                anos_inicio_act = row["AÑO INICIO"]
                anos_fin_act = row["AÑO FIN"]

                rangos_ajustados_html = []

                for rango, color in COLORES.items():
                    rango_inicio_def = rango[0]
                    rango_fin_def = rango[1]

                    if isinstance(rango_inicio_def, int):
                        try:
                            overlap_start = max(rango_inicio_def, int(anos_inicio_act))
                            overlap_end = min(rango_fin_def, int(anos_fin_act))
                            if overlap_start <= overlap_end:
                                rangos_ajustados_html.append(
                                    f"<span style='background-color: {color}; color: black; padding: 2px 4px; border-radius: 4px; font-weight: bold; margin-right: 2px;'>{overlap_start}-{overlap_end}</span>"
                                )
                        except ValueError:
                            continue
                    else:
                        if anos_inicio_act == rango_inicio_def:
                            rangos_ajustados_html.append(
                                f"<span style='background-color: {color}; color: white; padding: 2px 4px; border-radius: 4px; font-weight: bold; margin-right: 2px;'>{rango_inicio_def}</span>"
                            )

                iconos_html = ""
                if row.get("WIFI", ""):
                    iconos_html += f"<i class='fa-solid fa-wifi' style='color: {COLOR_AZUL_OSCURO};' title='Requiere clave Wifi'></i>&nbsp;"
                if row.get("DISPOSITIVO", ""):
                    iconos_html += f"<i class='fa-solid fa-mobile-screen' style='color: {COLOR_AZUL_OSCURO};' title='Requiere dispositivo del socio'></i>&nbsp;"

                etiquetas_html = ""
                if iconos_html or rangos_ajustados_html:
                    etiquetas_html = (
                        "<br>" + iconos_html + "".join(rangos_ajustados_html)
                    )

                profesor_html = ""
                if row["profesores"]:
                    profesor_html = f"<span style='font-size: small;'>{row['profesores']}</span><br>"

                descripcion_html = ""
                if row["DESCRIPCION"]:
                    descripcion_html = f"title='{row['DESCRIPCION']}'"

                # Reemplazar saltos de línea del CSV con <br> para HTML
                actividad_con_saltos = (
                    row["ACTIVIDAD"].replace("\n", "<br>").replace("\r", "")
                )

                contenido_actividad = f"{profesor_html}<b {descripcion_html}>{actividad_con_saltos}</b>{etiquetas_html}"

                hora_inicio_act = datetime.strptime(row["HORA_INICIO_STR"], "%H:%M")
                hora_fin_act = datetime.strptime(row["HORA_FIN_STR"], "%H:%M")

                for col_name, (start_str, end_str) in horarios_fijos.items():
                    hora_inicio_col = datetime.strptime(start_str, "%H:%M")
                    hora_fin_col = datetime.strptime(end_str, "%H:%M")

                    if col_name == "11:05 - 11:30":
                        final_schedule.loc[loc_tuple, col_name] = "Descanso"
                        continue

                    if (
                        hora_inicio_act >= hora_inicio_col
                        and hora_inicio_act < hora_fin_col
                    ):
                        if hora_fin_act <= hora_fin_col:
                            final_schedule.loc[loc_tuple, col_name] = (
                                contenido_actividad
                            )
                        else:
                            final_schedule.loc[loc_tuple, col_name] = (
                                contenido_actividad
                            )
                            horarios_list = list(horarios_fijos.keys())
                            current_col_index = horarios_list.index(col_name)
                            for next_col_name in horarios_list[current_col_index + 1 :]:
                                next_start_str, next_end_str = horarios_fijos[
                                    next_col_name
                                ]
                                next_hora_inicio_col = datetime.strptime(
                                    next_start_str, "%H:%M"
                                )
                                if hora_fin_act > next_hora_inicio_col:
                                    final_schedule.loc[loc_tuple, next_col_name] = (
                                        f"<b>{row['ACTIVIDAD']}</b> <br> continuación"
                                    )
                                    if hora_fin_act <= datetime.strptime(
                                        next_end_str, "%H:%M"
                                    ):
                                        break

            final_schedule = final_schedule.reset_index()

            # Calcular rowspan para ESCUELA y EDIFICIO
            final_schedule["rowspan_escuela"] = final_schedule.groupby("ESCUELA")[
                "ESCUELA"
            ].transform("count")
            final_schedule["rowspan_edificio"] = final_schedule.groupby(
                ["ESCUELA", "EDIFICIO"]
            )["EDIFICIO"].transform("count")

            html_output = generar_html_tabla(
                final_schedule,
                horarios_fijos,
                anio_nacimiento=None,
                anio_academico=anio_academico,
            )

            with open("horario.html", "w", encoding="utf-8") as f:
                f.write(html_output)
            print("🎉 Tabla de horario completa generada y guardada en 'horario.html'")

        elif anio_fin is None:
            print(
                f"🔍 Generando horario para el año de nacimiento: {anio_nacimiento}..."
            )
            html_output, filename = generar_horario_para_anio(
                df, anio_nacimiento, horarios_fijos, anio_academico
            )
            if html_output:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html_output)
                print(f"🎉 Tabla de horario generada y guardada en '{filename}'")
        else:
            print(
                f"🔍 Generando horarios para el rango de años: {anio_nacimiento} a {anio_fin}..."
            )
            for anio in range(anio_nacimiento, anio_fin + 1):
                html_output, filename = generar_horario_para_anio(
                    df, anio, horarios_fijos, anio_academico
                )
                if html_output:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(html_output)
                    print(f"  ✅ '{filename}' generado correctamente.")
            print(
                f"🎉 ¡Generación de horarios completada para el rango de {anio_nacimiento} a {anio_fin}!"
            )

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo CSV en la ruta {csv_path}.")
    except Exception as e:
        print(f"⚠️ Ocurrió un error al procesar el archivo CSV: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera un horario HTML a partir de un archivo CSV de actividades. Puede filtrar por un año de nacimiento o un rango."
    )
    parser.add_argument(
        "--anio_nacimiento",
        "-a",
        help="Año de nacimiento para filtrar las actividades (opcional). Puede ser un año o 'TUTORES' o 'ADULTOS AVAST'.",
    )
    parser.add_argument(
        "--anio_fin",
        "-b",
        type=int,
        help="Año de nacimiento final del rango para filtrar actividades. Requiere --anio_nacimiento para funcionar si este es un número.",
    )
    args = parser.parse_args()

    # Convertir el argumento de año a entero si es posible, si no, se queda como string
    try:
        anio_inicio = (
            int(args.anio_nacimiento)
            if args.anio_nacimiento and args.anio_nacimiento.isdigit()
            else args.anio_nacimiento
        )
    except (ValueError, TypeError):
        anio_inicio = args.anio_nacimiento

    csv_path = os.path.join(os.path.dirname(__file__), "actividades.csv")
    generar_horario_final(csv_path, anio_inicio, args.anio_fin)
