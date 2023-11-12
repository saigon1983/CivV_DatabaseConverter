from SQL_Module.sql_main import *
from Main_Module.constants import *

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
	SecondaryTablePrefixes = {'Units': 'Unit',
							  'Buildings': 'Building'}
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

			if tablename not in cls.DatabaseTableNames:
				raise ValueError('Таблицы с именем <{}> нет в оригинальной базе данных!'.format(tablename))
			cls.ValidTables[tablename] = {}

			sqlfile = SQLDBFILE
			i1 = sqlfile.find('CREATE TABLE IF NOT EXISTS "{}" ('.format(tablename))
			i2 = sqlfile[i1:].find(');')
			sqlfile = sqlfile[i1:i1+i2].splitlines()

			columnName 		= None
			dataType 		= None
			defaultValue 	= None


			for line in sqlfile[1:]:
				line = line.strip().rstrip(',')
				subline = line.split('\t')
				if line.startswith('"'):
					columnName = subline[0].strip('"')
					subline = subline[1:]
					if subline[0].strip("'").startswith('text'):
						print(columnName, subline)

				elif line.startswith('FOREIGN KEY'):
					pass
				else:
					pass

	def __init__(self, someData):
		for key, value in someData.items():
			if key == 'EntityType':
				if not self.__class__.MainTableName: self.set_main_table_name(value)
			if key == 'TableNames':
				if not self.__class__.ValidTables:
					self.set_valid_tables(value)
					print(self.ValidTables)