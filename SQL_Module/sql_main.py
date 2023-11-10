import sqlite3

def get_row_names(tablename, database = 'Original/Database/Civ5DebugDatabase.db'):
  connection = sqlite3.connect(database)
  connection.row_factory = sqlite3.Row
  cursor = connection.cursor()
  cursor = connection.execute('select * from {}'.format(tablename))
  row = cursor.fetchone()
  names = row.keys()
  connection.close()
  return names

def get_table_names(database = 'Original/Database/Civ5DebugDatabase.db'):
  connection = sqlite3.connect(database)
  cursor = connection.cursor()
  cursor.execute('SELECT name from sqlite_master where type= "table"')
  return [item[0] for item in cursor.fetchall()]

rows = get_row_names('Units')
tables = get_table_names()
print(tables)