import base64
import json
import os

import requests


def actualizar_contenido_wordpress(
    tipo_contenido,
    id_contenido,
    usuario,
    contrasena_app,
    ruta_archivo_html,
    url_sitio,
    texto_introduccion="",
):
    """
    Actualiza el contenido de una entrada o página de WordPress, añadiendo un texto de introducción.
    """
    if tipo_contenido not in ["posts", "pages"]:
        print("❌ Error: 'tipo_contenido' debe ser 'posts' o 'pages'.")
        return

    try:
        # Leer el contenido del archivo HTML
        if not os.path.exists(ruta_archivo_html):
            raise FileNotFoundError

        with open(ruta_archivo_html, encoding="utf-8") as f:
            contenido_html = f.read()

        # Concatenar el texto de introducción y el contenido del HTML
        nuevo_contenido_completo = f"{texto_introduccion}\n<br><br>{contenido_html}"

        # Codificar las credenciales para la autenticación Basic
        credenciales = f"{usuario}:{contrasena_app}"
        token = base64.b64encode(credenciales.encode("utf-8"))

        headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "Content-Type": "application/json",
        }

        # Construir la URL de la API de forma dinámica
        url_api = f"{url_sitio}/wp-json/wp/v2/{tipo_contenido}/{id_contenido}"

        # Datos a enviar a la API
        datos = {"content": nuevo_contenido_completo}

        print(f"--- Actualizando {tipo_contenido[:-1]} con ID: {id_contenido} ---")
        respuesta = requests.post(url_api, headers=headers, data=json.dumps(datos))

        if respuesta.status_code == 200:
            print(f"✅ ¡{tipo_contenido[:-1].capitalize()} actualizada correctamente!")
            print(f"URL del contenido: {respuesta.json()['link']}\n")
        else:
            print(f"❌ Error al actualizar. Código de estado: {respuesta.status_code}")
            print(f"Mensaje de error de la API: {respuesta.text}\n")

    except FileNotFoundError:
        print(f"❌ Error: El archivo {ruta_archivo_html} no se encontró.\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}\n")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}\n")


# --- Bloque principal para leer el JSON y ejecutar la función ---
if __name__ == "__main__":
    try:
        # CAMBIO AQUÍ: Ahora lee 'wordpress.json'
        with open("wordpress.json", encoding="utf-8") as f:
            configuracion = json.load(f)

        for item in configuracion:
            # Extraer las variables del diccionario y llamar a la función
            actualizar_contenido_wordpress(
                tipo_contenido=item.get("tipo_contenido"),
                id_contenido=item.get("id_contenido"),
                usuario=item.get("usuario"),
                contrasena_app=item.get("contrasena_app"),
                ruta_archivo_html=item.get("ruta_archivo_html"),
                url_sitio=item.get("url_sitio"),
                texto_introduccion=item.get("texto_introduccion", ""),
            )

    except FileNotFoundError:
        print(
            "❌ Error: El archivo 'wordpress.json' no se encontró. Asegúrate de que existe en el mismo directorio."
        )
    except json.JSONDecodeError:
        print("❌ Error: El archivo 'wordpress.json' no tiene un formato JSON válido.")
    except Exception as e:
        print(f"❌ Ocurrió un error al procesar el archivo de configuración: {e}")
