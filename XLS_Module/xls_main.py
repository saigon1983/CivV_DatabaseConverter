import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string

DB_ORIGINAL_PATH = r'Original/Tables'
DB_MODIFIED_PATH = r'Modified/Tables'

def open_table(tablename, path):
	# Возвращает любой открытый excel-файл с указанным названием по указанному пути
	return openpyxl.load_workbook(r'{}/{}'.format(path, tablename))
def open_original_table(tablename):
	# Возвращает оригинальную таблицу по названию без префиксов и расширений файла
	return openpyxl.load_workbook(r'{}/NewTU_{}_ORG.xlsx'.format(DB_ORIGINAL_PATH, tablename))
def open_modified_table(tablename):
	# Возвращает модифицированную таблицу по названию без префиксов и расширений файла
	return openpyxl.load_workbook(r'{}/NewTU_{}_ORG.xlsx'.format(DB_MODIFIED_PATH, tablename))
def get_tables(tablename, original = True):
	# Возвращает оригинальную или модифицированную таблицу по названию без префиксов и расширений файла
	return open_original_table(tablename) if original else open_modified_table(tablename)
def get_main_table(tablename, original = True):
	# Возвращает главную таблицу для указанного типа сущностей
	WB = get_tables(tablename, original)
	WS = WB[WB.sheetnames[0]]
	return WS
def get_secondary_table(tablename, sheetname, original = True):
	# Возвращает второстепенную таблицу для указанного типа сущностей по названию этой таблицы
	WB = get_tables(tablename, original)
	WS = WB[sheetname]
	return WS
def get_main_table_headers(tablename, original = True):
	# Возвращает словарь заголовков для главной оригинальной или модифицированной таблицы
	WS = get_main_table(tablename, original)
	first_row = WS[1]
	labels = {}
	pos = 0
	for cell in first_row:
		pos += 1
		labels[cell.value] = pos
	return labels
def select_all_entities(tablename, original = True):
	WB = get_tables(tablename, original)
	WS = WB[WB.sheetnames[0]]
	HEADERS  = {}
	ENTITIES = {}
	for cell in WS[1]: HEADERS[cell.value] = cell.column

	for row_index in range(3, WS.max_row+1):
		entity_name = WS[row_index][HEADERS['Type']-1].value
		ENTITIES[entity_name] = {'EntityType': tablename,
								 'TableNames': WB.sheetnames}
		for key, val in HEADERS.items():
			address = '{}{}'.format(get_column_letter(val), row_index)
			if key: ENTITIES[entity_name][key] = WS[address].value
	return ENTITIES