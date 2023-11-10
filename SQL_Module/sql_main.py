import sqlite3
import pandas as pd

def get_row_names(tablename, database = 'Original/Database/Civ5DebugDatabase.db'):
  connection = sqlite3.connect(database)
  connection.row_factory = sqlite3.Row
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

def get_column_properties(tablename, columnname, database = 'Original/Database/Civ5DebugDatabase.db'):
  connection = sqlite3.connect(database)
  list_of_columns = connection.execute("PRAGMA table_info('{}')".format(tablename)).fetchall()
  connection.close()
  columns_dict = {}
  for col in list_of_columns:
    columns_dict[col[1]] = col[2:-1]
    if col[1] == columnname: break
  return columns_dict[columnname]

def get_column_valuetype(tablename, columnname, database = 'Original/Database/Civ5DebugDatabase.db'):
  pass

def list_column_properties(tablename, columnname, database = 'Original/Database/Civ5DebugDatabase.db'):
  connection = sqlite3.connect(database)

rows = get_row_names('Units')
tables = get_table_names()
print(tables)

#connection = sqlite3.connect('Original/Database/Civ5DebugDatabase.db')
#info = connection.execute("PRAGMA table_info('Buildings')").fetchall()
#df = pd.DataFrame(info, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
#df = pd.read_sql("PRAGMA table_info('Units')", connection)
#connection.close()
#print(df)

print(get_column_properties('Policies', 'ID'))
