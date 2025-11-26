import sqlite3

conn = sqlite3.connect('db_temp.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tablas en la base de datos:")
print("-" * 50)
for table in tables:
    print(f"  - {table[0]}")
    
print("\n" + "=" * 50)
print("Detalles de cada tabla:")
print("=" * 50 + "\n")

for table in tables:
    table_name = table[0]
    print(f"\nTabla: {table_name}")
    print("-" * 50)
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"  Total de registros: {count}")

conn.close()
