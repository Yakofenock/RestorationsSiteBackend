from psycopg2 import connect

from Site.settings import CONFIG

con = connect(
    database=CONFIG.get('Postgres DB', 'name'),
    user=CONFIG.get('Postgres DB', 'user'),
    password=CONFIG.get('Postgres DB', 'password'),
    host=CONFIG.get('Postgres DB', 'host'),
    port=CONFIG.get('Postgres DB', 'port')
)
con.set_isolation_level(0)


cur = con.cursor()
cur.execute('SELECT * FROM "Payments"')
results = cur.fetchall()
print('Payments:')
[print(paiment) for paiment in results]
print()

cur.execute('SELECT * FROM "Restorations"')
results = cur.fetchall()
print('Restorations:')
[print(soft) for soft in results]