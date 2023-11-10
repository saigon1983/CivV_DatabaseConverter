import sqlite3

connection = sqlite3.connect('Original/Database/Civ5DebugDatabase.db')
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor = connection.execute('select * from buildings')
cursor = connection.execute("SELECT name, type FROM pragma_table_info('buildings')")
results = cursor.description
row = cursor.fetchone()
names = row.keys()

print(names)



connection.close()

def get_row_names(tablename, database = 'Original/Database/Civ5DebugDatabase.db'):

  pass