import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string

DB_ORIGINAL_PATH = r'Original/Tables'
DB_MODIFIED_PATH = r'Modified/Tables'

SecondaryTablePrefixes = {'BuildingClasses': 	'BuildingClass',
						  'Buildings': 			'Building',
						  'Civilizations': 		'Civilization',
						  'Eras': 				'Era',
						  'Features': 			'Feature',
						  'Improvements': 		'Improvement',
						  'Leaders': 			'Leader',
						  'Policies': 			'Policy',
						  'PolicyBranchTypes': 	'PolicyBranch',
						  'Resources': 			'Resource',
						  'Technologies': 		'Technology',
						  'UnitClasses': 		'UnitClass',
						  'Units': 				'Unit'}

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
	WSprimary 	= WB[WB.sheetnames[0]]
	WSsecondary = WB.sheetnames[1:]
	HEADERS  = {}
	ENTITIES = {}
	for cell in WSprimary[1]: HEADERS[cell.value] = cell.column

	for row_index in range(3, WSprimary.max_row+1):
		entity_name = WSprimary[row_index][HEADERS['Type']-1].value
		ENTITIES[entity_name] = {'EntityType': tablename,
								 'TableNames': WB.sheetnames}
		for key, val in HEADERS.items():
			address = '{}{}'.format(get_column_letter(val), row_index)
			if key: ENTITIES[entity_name][key] = WSprimary[address].value

	for key in ENTITIES.keys():
		ENTITIES[key]['SecondaryTables'] = {}
		for tableName in ENTITIES[key]['TableNames'][1:]:
			ENTITIES[key]['SecondaryTables'][tableName] = []

	for secondary in WSsecondary:
		WS = WB[secondary]
		WStype = WS['A2'].value
		if WStype == 'OneType_OneStatement':
			tagMain 	= WS['A1'].value
			tagSecond 	= WS['B1'].value
			for rowNum in range(3, WS.max_row+1):
				someType  = WS['A{}'.format(rowNum)].value
				someValue = WS['B{}'.format(rowNum)].value
				if someValue:
					ENTITIES[someType]['SecondaryTables'][secondary].append(someValue)
					print(ENTITIES[someType])
					#print(secondary, someType, someValue)
		else:
			pass

		#if WStype: print(secondary, WStype)
	return ENTITIES

def get_proper_subtable_name(mainTableName, tablename):
	result = '{}_{}'.format(SecondaryTablePrefixes[mainTableName], tablename)
	tablename = tablename
	if result == 'Building_DomainFreeExperiencePerGW': 		result = 'Building_DomainFreeExperiencePerGreatWork'
	if result == 'Policy_BuildinClassProductionModifiers': 	result = 'Policy_BuildingClassProductionModifiers'
	if result == 'Feature_FakeFeatures': 					result = 'FakeFeatures'
	return result
def parse_excel_Civ5_table(tablename, original = True):
	# Метод для парсинга всей заданной таблицы
	workbook = get_tables(tablename, original)	# Получаем объект excel-файла для обработки
	mainTableName  = workbook.sheetnames[0]		# Название главной таблицы
	subTableNames  = workbook.sheetnames[1:]		# Названия второстепенных таблиц
	properSubNames = [get_proper_subtable_name(mainTableName, x) for x in subTableNames]

	ENTITIES = {} # результирующий словарь всех сущностей, представленных в таблице

	# Первым делом обрабатываем главную таблицу, чтобы создать все необходимые сущности и заполнить их основные характеристики
	mainTable = workbook[mainTableName]
	headers   = {}
	for cell in mainTable[1]: headers[cell.value] = cell.column

	for row_index in range(3, mainTable.max_row + 1):
		name 		= mainTable[row_index][headers['Type'] - 1].value
		ENTITIES[name] = {'EntityType': mainTableName,
						  'TableNames': properSubNames,
						  'Subtables':	{}}
		for subtablename in ENTITIES[name]['TableNames']:
			ENTITIES[name]['Subtables'][subtablename] = {'TableType': 	None,
														 'TableValues':	[]}
		for key, val in headers.items():
			address = '{}{}'.format(get_column_letter(val), row_index)
			if key: ENTITIES[name][key] = mainTable[address].value
	# Приступаем к обработке второстепенных таблиц
	for subtablename in subTableNames:
		subTable 	 	= workbook[subtablename]
		subTableKey  	= get_proper_subtable_name(mainTableName, subtablename)
		subTableType 	= subTable['A2'].value
		subTableValues 	= {}

		if subTableType == 'OneType_OneStatement':
			for rowNum in range(3, subTable.max_row + 1):
				entityType	= subTable['A{}'.format(rowNum)].value
				properValue	= subTable['B{}'.format(rowNum)].value
				if properValue:
					if subTableKey not in ENTITIES[entityType]['Subtables'].keys(): raise TypeError
					ENTITIES[entityType]['Subtables'][subTableKey]['TableType'] = subTableType
					ENTITIES[entityType]['Subtables'][subTableKey]['TableValues'].append(properValue)
		elif subTableType == 'OneType_PredefineStatement':
			valuesRange = range(2, subTable.max_column + 1)
			thisHeaders = {}
			for cell in subTable[1]: thisHeaders[cell.value] = cell.column
			print(thisHeaders)
			print(subTableKey, valuesRange)
		else:
			pass

	return ENTITIES