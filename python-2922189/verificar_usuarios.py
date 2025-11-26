import sqlite3

conn = sqlite3.connect('db_temp.sqlite3')
cursor = conn.cursor()

print("=" * 60)
print("USUARIOS EN TABLA 'usuarios' (Tu modelo custom)")
print("=" * 60)
cursor.execute('SELECT id_usu, nombres, apellidos, correo, rol, documento FROM usuarios')
usuarios = cursor.fetchall()
for u in usuarios:
    print(f"ID: {u[0]} | {u[1]} {u[2]} | {u[3]} | Rol: {u[4]} | Doc: {u[5]}")

print("\n" + "=" * 60)
print("USUARIOS EN TABLA 'auth_user' (Sistema de Django)")
print("=" * 60)
cursor.execute('SELECT id, username, email, is_superuser, is_staff, is_active FROM auth_user')
auth_users = cursor.fetchall()
for u in auth_users:
    print(f"ID: {u[0]} | Username: {u[1]} | Email: {u[2]} | Super: {u[3]} | Staff: {u[4]} | Activo: {u[5]}")

conn.close()
