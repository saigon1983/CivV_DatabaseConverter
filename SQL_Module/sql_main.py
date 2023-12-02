import sqlite3
from Main_Module.constants import *

def get_row_names(tablename, database='Original/Database/Civ5DebugDatabase.db'):
    # Возвращает список наименований столбцов таблицы
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    cursor = connection.execute('select * from {}'.format(tablename))
    row = cursor.fetchone()
    names = row.keys()
    connection.close()
    return names
def get_table_names(database='Original/Database/Civ5DebugDatabase.db'):
    # Возвращает список доступных таблиц в указанной базе данных
    connection = sqlite3.connect(database)
    cursor = connection.cursor()
    cursor.execute('SELECT name from sqlite_master where type= "table"')
    connection.close()
    return [item[0] for item in cursor.fetchall()]
def get_column_properties(tablename, columnname, database='Original/Database/Civ5DebugDatabase.db'):
    # Возвращает кортеж из значений трех свойств колонки: тип значения, not_null и значение по умолчанию
    connection = sqlite3.connect(database)
    list_of_columns = connection.execute("PRAGMA table_info('{}')".format(tablename)).fetchall()
    connection.close()
    columns_dict = {}
    for col in list_of_columns:
        columns_dict[col[1]] = col[2:-1]
        if col[1] == columnname:
            break
    return columns_dict[columnname]
def get_column_valuetype(tablename, columnname, database='Original/Database/Civ5DebugDatabase.db'):
    # Возвращает тип значения для указанной колонки указанной таблицы указанной базы данных
    return get_column_properties(tablename, columnname, database)[0]
def get_column_default(tablename, columnname, database='Original/Database/Civ5DebugDatabase.db'):
    # Возвращает значение по умолчанию для указанной колонки указанной таблицы указанной базы данных
    # Если тип значения при этом равен <boolean>, то преобразует вывод в <true> или <false>
    default = get_column_properties(tablename, columnname, database)[2]
    if get_column_valuetype(tablename, columnname, database) == 'boolean':
        default = 'false' if default == 0 else 'true'
    return default

def db_get_value_from_cell(table, column, termName, termValue):
    name = column if column != 'Unique' else f'"{column}"'
    request = f"SELECT {name} FROM {table} WHERE {termName} = '{termValue}'"
    result = DB_ORIGINAL.execute(request).fetchone()[0]
    return result

def db_get_values_from_row(table, pairs):
    array = []
    for title, value in pairs.items():
        array.append(f"{title} = '{value}'")
    request = f"SELECT * FROM {table} WHERE {' AND '.join(array)} "
    result = DB_ORIGINAL.execute(request).fetchall()
    if len(result) > 1: result = [result[-1]]
    return tuple(result[0]) if result else ()
def db_get_pair_of_values_from_row(table, pairs, column):
    array = []
    for title, value in pairs.items():
        array.append(f"{title} = '{value}'")
    request = f"SELECT {column} FROM {table} WHERE {' AND '.join(array)} "
    result = DB_ORIGINAL.execute(request).fetchall()
    if len(result) > 1: result = [result[-1]]
    return {column: tuple(result[0])[0] if result else None}
