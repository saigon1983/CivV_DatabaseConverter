from SQL_Module.sql_main import *
from Main_Module.constants import *
import re

class CivValue:

	def __init__(self, table, owner, name, value):
		self.table  	= table
		self.owner		= owner
		self.name  		= name
		self.value 		= value
		#self.__setup()

	def __setup(self):
		if self.name != 'ID':
			list_of_columns = DB_ORIGINAL.execute("SELECT type, dflt_value, pk FROM pragma_table_info('{}') WHERE name = '{}'".format(self.table, self.name)).fetchone()
		else:
			list_of_columns = ('INTEGER', None, 1)
		self.valueType 	= list_of_columns[0]
		self.default 	= list_of_columns[1]
		self.primary 	= list_of_columns[2]

		if self.name != 'ID':
			if self.valueType == 'INTEGER':
				if self.default.startswith("'-"): self.default = self.default.replace("'", '')
				self.default = int(self.default)
			elif self.valueType == 'TEXT':
				if self.default:
					pass
				else:
					print(self.name, self.value, self.default)
			elif self.valueType == 'boolean':
				self.valueType = 'BOOLEAN'

	def __str__(self):
		return 'Value from table <{}> of owner <{}>:\t{}: {}'.format(self.table, self.owner, self.name, self.value)

class CivEntity:
	# Общий родительский класс для всех типов сущностей Civilization 5
	MAIN_TABLE    = ''
	OTHER_TABLES  = []
	def __init__(self, entityData):
		if not self.__class__.MAIN_TABLE:
			self.__class__.MAIN_TABLE = entityData['EntityType']
		if not self.__class__.OTHER_TABLES:
			self.__class__.OTHER_TABLES = entityData['TableNames'].copy()
			if self.__class__.MAIN_TABLE in self.__class__.OTHER_TABLES:
				self.__class__.OTHER_TABLES.remove(self.__class__.MAIN_TABLE)
		self.Type = entityData['Type']

		for key, value in entityData.items():
			if key not in ('EntityType', 'TableNames', 'Type'):
				newValue = CivValue(self.MAIN_TABLE, self.Type, key, value)
				self.__setattr__(key, newValue)
				#print(self.__getattribute__(key))

		self.__check_origin()

	def __check_origin(self):
		tabletypes = [item[0] for item in DB_ORIGINAL.execute("select Type from {}".format(self.MAIN_TABLE)).fetchall()]
		self.original = self.Type in tabletypes

class Civ5Entity:
	# Общий родительский класс для всех типов сущностей Civilization 5
	DB 	= sqlite3.connect('Original/Database/Civ5DebugDatabase.db')
	MainTableName 		= ''	# Название основной таблицы (тип сущности)
	DatabaseTableNames 	= [item[0] for item in DB.execute('SELECT name from sqlite_master where type= "table"').fetchall()]
	SecondaryTablePrefixes = {'BuildingClasses': 'BuildingClass',
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
	ValidTables 		= {}	# Словарь названий допустимых таблиц, в которых может быть отредактирована сущность.
								# Ключами являются названия таблиц, а значениями - вложенные списки, где ключами являются
								# заголовки свойств (столбцов), а их значениями - параметры этих заголовков в БД SQL

	@classmethod
	def set_main_table_name(cls, value):
		cls.MainTableName = value
	@classmethod
	def set_valid_tables(cls, value):
		tablenames = value.copy()
		for tablename in tablenames:
			if tablename != cls.MainTableName:
				prefix = cls.SecondaryTablePrefixes[cls.MainTableName]
				tablename = '{}_{}'.format(prefix, tablename)

				if tablename == 'Building_DomainFreeExperiencePerGW': tablename = 'Building_DomainFreeExperiencePerGreatWork'
				if tablename == 'Feature_FakeFeatures': tablename = 'FakeFeatures'
				if tablename == 'Policy_BuildinClassProductionModifiers': tablename = 'Policy_BuildingClassProductionModifiers'

			if tablename not in cls.DatabaseTableNames:
				raise ValueError('Таблицы с именем <{}> нет в оригинальной базе данных!'.format(tablename))
			cls.ValidTables[tablename] = {}

			sqlfile = SQLDBFILE
			i1 = sqlfile.find('CREATE TABLE IF NOT EXISTS "{}" ('.format(tablename))
			i2 = sqlfile[i1:].find(');')
			sqlfile = sqlfile[i1:i1+i2].splitlines()

			for line in sqlfile[1:]:
				columnName 		= None
				dataType 		= None
				defaultValue	= None
				notNull			= False
				unique			= False

				line = line.strip().rstrip(',')
				match = re.match(r'"\S+"\t', line)
				if match:
					line = line.replace(match[0], '').strip()
					columnName = match[0][1:-2]
				if line.startswith('FOREIGN KEY'):
					match = re.match(r'FOREIGN KEY\("\S+"\)', line)[0]
					line = line.replace(match, '').strip()
					match = match.replace('FOREIGN KEY("', '').replace('")', '').strip()
					columnName = match
				if line.startswith('PRIMARY KEY'):
					line = line.replace('PRIMARY KEY', '').strip('(').strip(')').strip()
					match = re.match(r'"\S+"', line)[0]
					line = line.replace(match, '').strip()
					columnName = match.replace('"', '')
				if not columnName: raise ValueError
				if columnName not in cls.ValidTables[tablename].keys():
					cls.ValidTables[tablename][columnName] = {'DataType': 		None,
															  'DefaultValue': 	None,
															  'References': 	None,
															  'AutoIncrement': 	None,
															  'NotNull': 		None,
															  'Unique': 		None}
				if line.startswith('AUTOINCREMENT'):
					line = line.replace('AUTOINCREMENT', '').strip()
					cls.ValidTables[tablename][columnName]['AutoIncrement'] = True
				if line.startswith('REFERENCES'):
					match = re.match(r'REFERENCES "\S+"\("\S+"\)', line)[0]
					line = line.replace(match, '').strip()
					match = match.replace('REFERENCES "', '').replace('")', ')').replace('"("', '(').strip()
					cls.ValidTables[tablename][columnName]['References'] = match
				if line.startswith('text'):
					dataType = 'TEXT'
					line = line.replace('text', '').strip()
				if line.startswith('integer') or line.startswith('int'):
					dataType = 'INTEGER'
					line = line.replace('integer', '').replace('int', '').strip()
				if line.startswith('boolean') or line.startswith('bool'):
					dataType = 'BOOLEAN'
					line = line.replace('boolean', '').replace('bool', '').strip()
				if not cls.ValidTables[tablename][columnName]['DataType']:
					cls.ValidTables[tablename][columnName]['DataType'] = dataType
				if line.startswith('DEFAULT'):
					line = line.replace('DEFAULT', '').strip()
					if line == '0' and dataType == 'BOOLEAN':
						defaultValue = 'false'
						line = line.replace('0', '').strip()
					if line == '1' and dataType == 'BOOLEAN':
						defaultValue = 'true'
						line = line.replace('1', '').strip()
					if line == 'NULL' and dataType == 'TEXT':
						defaultValue = 'NULL'
						line = line.replace(defaultValue, '').strip()
					if line == "'-1'" and dataType == 'INTEGER':
						defaultValue = -1
						line = line.replace("'-1'", '').strip()
					try:
						defaultValue = int(line)
						line = line.replace(str(defaultValue), '').strip()
					except: pass
					if line.startswith("'"):
						defaultValue = line.strip("'")
						line = line.replace(defaultValue, '').replace("'", '').strip()
				if not cls.ValidTables[tablename][columnName]['DefaultValue']:
					cls.ValidTables[tablename][columnName]['DefaultValue'] = defaultValue
				if line.startswith('NOT NULL'):
					line = line.replace("NOT NULL", '').strip()
					notNull = True
				if line.startswith('UNIQUE'):
					line = line.replace("UNIQUE", '').strip()
					unique = True
				cls.ValidTables[tablename][columnName]['NotNull'] 		= notNull
				cls.ValidTables[tablename][columnName]['Unique'] 		= unique
				if line:
					raise ValueError

	def __init__(self, someData):
		for key, value in someData.items():
			if key == 'EntityType':
				if not self.__class__.MainTableName: self.set_main_table_name(value)
			elif key == 'TableNames':
				if not self.__class__.ValidTables: self.set_valid_tables(value)
			else:
				curColumn 	= key
				curValue  	= value
				curAttribs	= self.ValidTables[self.MainTableName][key]

				if curAttribs['DataType'] == 'INTEGER':
					try: 	curValue = int(curValue)
					except: pass
					if curValue and type(curValue) != int: raise ValueError
				elif curAttribs['DataType'] == 'TEXT': pass
				elif curAttribs['DataType'] == 'BOOLEAN':
					if curValue not in ('false', 'true') and curValue != None:
						raise TypeError('Table <{}>: column <{}> has value <{}>. Must be in <<false, true>>'.format(self.MainTableName, curColumn, curValue))
				else: raise TypeError('Table <{}>: Unrecognized data type <{}> in column <{}>'.format(self.MainTableName, curAttribs['DataType'], curColumn))

				if curValue == None:
					#if curValue != curAttribs['DefaultValue']: print(self.MainTableName, curColumn, curValue, curAttribs['DefaultValue'])
					curValue = curAttribs['DefaultValue']
				if curValue == None:
					pass
					print(self.MainTableName, curColumn, curValue)
				print('====================================')

class BuildingClass(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Building(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Civilization(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Era(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Feature(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Improvement(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Leader(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Policy(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class PolicyBranch(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Resource(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Technology(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class UnitClass(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)
class Unit(Civ5Entity):
	MainTableName	= ''
	ValidTables 	= {}
	def __init__(self, someData):
		super().__init__(someData)