#!/usr/bin/env python

import argparse
import os
from datetime import datetime

import numpy as np
import pandas as pd

# Definición de los colores según el rango de edad (colores originales)
COLORES = {
    (2017, 2020): "#FCF37C",
    (2014, 2016): "#FCBB8B",
    (2011, 2013): "#81D3C9",
    (2003, 2010): "#EFC1FD",
}

# Colores de la paleta del logotipo
COLOR_AZUL_OSCURO = "#00546e"
COLOR_CIAN_BRILLANTE = "#00bac3"
COLOR_UBICACION_FONDO = "#9cc9d6"


def generar_html_tabla(df_grouped, horarios_fijos, anio_nacimiento):
    """
    Genera el HTML de la tabla de horario a partir de un DataFrame agrupado.
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
            /* Estilo para los rangos de edad para que el texto sea legible sobre el fondo */
            .actividad-cell span[style*="background-color"] {{
                color: black !important;
            }}
        </style>
    </head>
    <body>
    """
    if anio_nacimiento:
        html_output += (
            f"<div class='anio-header'>Horario para nacidos en {anio_nacimiento}</div>"
        )

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

    for (escuela, edificio, planta, aula), grupo in df_grouped:
        html_output += "<tr>"
        html_output += f"<td class='location-cell'><a href='https://asociacion-avast.org/ubicacion/' target='_blank' style='color: {COLOR_AZUL_OSCURO}; text-decoration: none;'>{escuela}</a></td>"
        html_output += f"<td class='location-cell'>{edificio}</td>"
        html_output += f"<td class='location-cell'>{planta}</td>"
        html_output += f"<td class='location-cell'>{aula}</td>"
        for col in horarios_fijos.keys():
            html_output += f"<td class='actividad-cell'>{grupo[col].iloc[0]}</td>"
        html_output += "</tr>"

    html_output += """
    </tbody>
    </table>
    </body>
    </html>
    """
    return html_output


def generar_horario_para_anio(df, anio_nacimiento, horarios_fijos):
    """
    Genera una tabla de horario en formato HTML para un año de nacimiento específico.
    """
    df_filtrado = df[
        (df["AÑO INICIO"] <= anio_nacimiento) & (df["AÑO FIN"] >= anio_nacimiento)
    ].copy()

    if df_filtrado.empty:
        print(
            f"❌ No se encontraron actividades para el año de nacimiento: {anio_nacimiento}"
        )
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

        anos_inicio_act = int(row["AÑO INICIO"])
        anos_fin_act = int(row["AÑO FIN"])

        rangos_ajustados_html = []
        colores_ordenados = sorted(COLORES.items(), key=lambda x: x[0][0])

        for rango, color in colores_ordenados:
            rango_inicio_def = rango[0]
            rango_fin_def = rango[1]

            overlap_start = max(rango_inicio_def, anos_inicio_act)
            overlap_end = min(rango_fin_def, anos_fin_act)

            if overlap_start <= overlap_end:
                rangos_ajustados_html.append(
                    f"<span style='background-color: {color}; color: black; padding: 2px 4px; border-radius: 4px; font-weight: bold; margin-right: 2px;'>{overlap_start}-{overlap_end}</span>"
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

        # ⚠️ Atributo title para la descripción sobre el nombre de la actividad
        descripcion_html = ""
        if row["DESCRIPCION"]:
            descripcion_html = f"title='{row['DESCRIPCION']}'"

        contenido_actividad = f"{profesor_html}<b {descripcion_html}>{row['ACTIVIDAD']}</b>{etiquetas_html}"

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
    df_grouped = final_schedule.groupby(["ESCUELA", "EDIFICIO", "PLANTA", "AULA"])

    html_output = generar_html_tabla(df_grouped, horarios_fijos, anio_nacimiento)
    output_filename = f"horario_filtrado-{anio_nacimiento}.html"
    return html_output, output_filename


def generar_horario_final(csv_path, anio_nacimiento=None, anio_fin=None):
    """
    Lee un CSV de actividades y genera una tabla de horario en HTML.
    Puede generar un solo horario o un rango de ellos.
    """
    try:
        # Se añaden las nuevas columnas a la lista de columnas requeridas
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
            "ACTIVIDAD",
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

        df["PLANTA"] = (
            pd.to_numeric(df["PLANTA"], errors="coerce").fillna(0).astype(int)
        )
        df["AÑO INICIO"] = (
            pd.to_numeric(df["AÑO INICIO"], errors="coerce").fillna(0).astype(int)
        )
        df["AÑO FIN"] = (
            pd.to_numeric(df["AÑO FIN"], errors="coerce").fillna(0).astype(int)
        )

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

            locations = df[["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]].drop_duplicates()
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
            for index, row in df.iterrows():
                loc_tuple = (
                    row["ESCUELA"],
                    row["EDIFICIO"],
                    row["PLANTA"],
                    row["AULA"],
                )

                anos_inicio_act = int(row["AÑO INICIO"])
                anos_fin_act = int(row["AÑO FIN"])

                rangos_ajustados_html = []
                colores_ordenados = sorted(COLORES.items(), key=lambda x: x[0][0])

                for rango, color in colores_ordenados:
                    rango_inicio_def = rango[0]
                    rango_fin_def = rango[1]

                    overlap_start = max(rango_inicio_def, anos_inicio_act)
                    overlap_end = min(rango_fin_def, anos_fin_act)

                    if overlap_start <= overlap_end:
                        rangos_ajustados_html.append(
                            f"<span style='background-color: {color}; color: black; padding: 2px 4px; border-radius: 4px; font-weight: bold; margin-right: 2px;'>{overlap_start}-{overlap_end}</span>"
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

                contenido_actividad = f"{profesor_html}<b {descripcion_html}>{row['ACTIVIDAD']}</b>{etiquetas_html}"

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
            df_grouped = final_schedule.groupby(
                ["ESCUELA", "EDIFICIO", "PLANTA", "AULA"]
            )

            html_output = generar_html_tabla(
                df_grouped, horarios_fijos, anio_nacimiento=None
            )

            with open("horario.html", "w", encoding="utf-8") as f:
                f.write(html_output)
            print("🎉 Tabla de horario completa generada y guardada en 'horario.html'")

        elif anio_fin is None:
            print(
                f"🔍 Generando horario para el año de nacimiento: {anio_nacimiento}..."
            )
            html_output, filename = generar_horario_para_anio(
                df, anio_nacimiento, horarios_fijos
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
                    df, anio, horarios_fijos
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
        type=int,
        help="Año de nacimiento para filtrar las actividades (opcional).",
    )
    parser.add_argument(
        "--anio_fin",
        "-b",
        type=int,
        help="Año de nacimiento final del rango para filtrar actividades. Requiere --anio_nacimiento para funcionar.",
    )
    args = parser.parse_args()

    csv_path = os.path.join(os.path.dirname(__file__), "actividades.csv")
    generar_horario_final(csv_path, args.anio_nacimiento, args.anio_fin)
