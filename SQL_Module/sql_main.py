import sqlite3


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
