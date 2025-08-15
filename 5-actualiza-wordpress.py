#!/usr/bin/env python
import base64
import json
import os

import requests


def actualizar_contenido_wordpress(
    id_contenido,
    ruta_archivo_html,
    url_sitio,
    usuario,
    contrasena_app,
    tipo_contenido,
    texto_introduccion="",
    texto_final="",
):
    """
    Actualiza el contenido de una entrada o página de WordPress.
    """
    if not os.path.exists(ruta_archivo_html):
        print(f"❌ Error: El archivo {ruta_archivo_html} no se encontró.\n")
        return

    try:
        with open(ruta_archivo_html, encoding="utf-8") as f:
            contenido_html = f.read()

        nuevo_contenido_completo = (
            f"{texto_introduccion}<br><br>{contenido_html}<br><br>{texto_final}"
        )

        credenciales = f"{usuario}:{contrasena_app}"
        token = base64.b64encode(credenciales.encode("utf-8"))

        headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "Content-Type": "application/json",
        }

        url_api = f"{url_sitio}/wp-json/wp/v2/{tipo_contenido}/{id_contenido}"

        datos = {"content": nuevo_contenido_completo}
        print(f"--- Actualizando {tipo_contenido[:-1]} con ID: {id_contenido} ---")
        respuesta = requests.post(url_api, headers=headers, data=json.dumps(datos))

        if respuesta.status_code == 200:
            print("✅ ¡Contenido actualizado correctamente!")
            print(f"URL del contenido: {respuesta.json()['link']}\n")
        else:
            print(f"❌ Error al actualizar. Código de estado: {respuesta.status_code}")
            print(f"Mensaje de error de la API: {respuesta.text}\n")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}\n")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}\n")


def reemplazar_archivo_wordpress(
    id_contenido, ruta_nuevo_archivo, url_sitio, usuario, contrasena_app
):
    """
    Reemplaza un archivo existente en la biblioteca de medios de WordPress.
    """
    if not os.path.exists(ruta_nuevo_archivo):
        print(f"❌ Error: El archivo {ruta_nuevo_archivo} no se encontró.\n")
        return

    try:
        credenciales = f"{usuario}:{contrasena_app}"
        token = base64.b64encode(credenciales.encode("utf-8"))

        url_api = f"{url_sitio}/wp-json/wp/v2/media/{id_contenido}"

        headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{os.path.basename(ruta_nuevo_archivo)}"',
        }

        with open(ruta_nuevo_archivo, "rb") as f:
            datos_binarios = f.read()

        print(f"--- Reemplazando el fichero con ID: {id_contenido} ---")
        respuesta = requests.post(url_api, headers=headers, data=datos_binarios)

        if respuesta.status_code == 200:
            print(f"✅ ¡Fichero con ID {id_contenido} reemplazado correctamente!")
            print(f"URL del fichero: {respuesta.json()['source_url']}\n")
        else:
            print(
                f"❌ Error al reemplazar el fichero. Código de estado: {respuesta.status_code}"
            )
            print(f"Mensaje de error de la API: {respuesta.text}\n")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}\n")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}\n")


if __name__ == "__main__":
    try:
        with open(".wordpressauth.json", encoding="utf-8") as f:
            credenciales_sitios = json.load(f)

        with open("wordpress.json", encoding="utf-8") as f:
            configuracion = json.load(f)

        for item in configuracion:
            tipo = item.get("tipo_contenido")
            url_sitio = item.get("url_sitio")

            auth = credenciales_sitios.get(url_sitio)
            if not auth:
                print(
                    f"❌ Error: No se encontraron credenciales para la URL: {url_sitio}\n"
                )
                continue

            usuario = auth.get("usuario")
            contrasena_app = auth.get("contrasena_app")

            if tipo in ["posts", "pages"]:
                actualizar_contenido_wordpress(
                    id_contenido=item.get("id_contenido"),
                    ruta_archivo_html=item.get("ruta_archivo_html"),
                    url_sitio=url_sitio,
                    usuario=usuario,
                    contrasena_app=contrasena_app,
                    tipo_contenido=tipo,  # Le pasamos 'posts' o 'pages' a la función
                    texto_introduccion=item.get("texto_introduccion", ""),
                    texto_final=item.get("texto_final", ""),
                )
            elif tipo == "media":
                reemplazar_archivo_wordpress(
                    id_contenido=item.get("id_contenido"),
                    ruta_nuevo_archivo=item.get("ruta_nuevo_archivo"),
                    url_sitio=url_sitio,
                    usuario=usuario,
                    contrasena_app=contrasena_app,
                )
            else:
                print(f"⚠️ Tipo de contenido desconocido en la configuración: {tipo}\n")

    except FileNotFoundError:
        print(
            "❌ Error: Uno de los archivos de configuración no se encontró. Asegúrate de que 'wordpress.json' y '.wordpressauth.json' existen en el mismo directorio."
        )
    except json.JSONDecodeError:
        print("❌ Error: Uno de los archivos JSON no tiene un formato válido.")
    except Exception as e:
        print(f"❌ Ocurrió un error al procesar la configuración: {e}")
