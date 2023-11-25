from SQL_Module.sql_main import *
from Main_Module.constants import *
import re

class Civ5Value:
	def __init__(self, name, value, attributes):
		self.name  		= name
		self.value 		= value
		if attributes == None: raise AttributeError('Список атрибутов, переданный для значения {} пуст!'.format(self.name))
		self.type 		= attributes['DataType']
		self.default 	= attributes['DefaultValue']
		self.reference 	= attributes['References']
		self.autoinc 	= attributes['AutoIncrement']
		self.notnull 	= attributes['NotNull']
		self.unique 	= attributes['Unique']

	def __str__(self):
		return '{}: {} ({}, {})'.format(self.name, self.value, self.type, self.is_default())
	def __repr__(self):
		return '{}: {} ({}, {})'.format(self.name, self.value, self.type, self.is_default())
	def is_default(self):
		return self.value == self.default

class Civ5ValuesGroup:
	def __init__(self, groupName, defaults):
		self.name   = groupName
		self.values = {}
		self.values['Default'] = []
		for valueName, thisValue in defaults.items():
			newValue = Civ5Value(valueName, thisValue['DefaultValue'], thisValue)
			self.values['Default'].append(newValue)
		self.values['Default'] = tuple(self.values['Default'])
	def insertValues(self, values):
		pass
class Civ5Entity:
	# Общий родительский класс для всех типов сущностей Civilization 5
	MainTableName 		= ''	# Название основной таблицы (тип сущности)
	OriginalEntities	= []	# Список оригинальных сущностей, доступных в немодифицированной игре
	SecondaryTablePrefixes = {'BuildingClasses': 	'BuildingClass',
							  'Buildings': 			'Building',
							  'Civilizations': 		'Civilization',
							  'Eras': 				'Era',
							  'Features': 			'Feature',
							  'FakeFeatures': 		'Feature',
							  'Improvements': 		'Improvement',
							  'Leaders': 			'Leader',
							  'Policies': 			'Policy',
							  'PolicyBranchTypes': 	'PolicyBranch',
							  'Resources': 			'Resource',
							  'Technologies': 		'Technology',
							  'UnitClasses': 		'UnitClass',
							  'Units': 				'Unit'}
	TableProperties 	= {}	# Словарь названий допустимых таблиц, в которых может быть отредактирована сущность.
								# Ключами являются названия таблиц, а значениями - вложенные списки, где ключами являются
								# заголовки свойств (столбцов), а их значениями - параметры этих заголовков в БД SQL

	@classmethod
	def getFamilyTableNames(cls, original=True):
		# Метод класса возвращает список названий таблиц, соответствующий сущности класса, начиная с главной таблицы
		CURRENT_DB = DB_ORIGINAL if original else DB_MODIFIED

		result 	= [cls.MainTableName]
		prefix 	= cls.SecondaryTablePrefixes[cls.MainTableName]
		pattern = "SELECT name FROM sqlite_master WHERE type='table' and name LIKE '{}\\_%' ESCAPE '\\'".format(prefix)

		for tablename in CURRENT_DB.execute(pattern).fetchall(): result.append(tablename[0])

		return result
	@classmethod
	def setFamilyTableProperties(cls):
		family_table_names = cls.getFamilyTableNames()
		for tablename in family_table_names:
			cls.TableProperties[tablename] = {}

			start  	= SQLDBFILE.find('CREATE TABLE IF NOT EXISTS "{}" ('.format(tablename))
			finish 	= start+SQLDBFILE[start:].find(');')
			sqlfile = SQLDBFILE[start:finish].splitlines()
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
				if columnName not in cls.TableProperties[tablename].keys():
					cls.TableProperties[tablename][columnName] = {'DataType': 		None,
															  'DefaultValue': 	None,
															  'References': 	None,
															  'AutoIncrement': 	None,
															  'NotNull': 		None,
															  'Unique': 		None}
				if line.startswith('AUTOINCREMENT'):
					line = line.replace('AUTOINCREMENT', '').strip()
					cls.TableProperties[tablename][columnName]['AutoIncrement'] = True
				if line.startswith('REFERENCES'):
					match = re.match(r'REFERENCES "\S+"\("\S+"\)', line)[0]
					line = line.replace(match, '').strip()
					match = match.replace('REFERENCES "', '').replace('")', ')').replace('"("', '(').strip()
					cls.TableProperties[tablename][columnName]['References'] = match
				if line.startswith('text'):
					dataType = 'TEXT'
					line = line.replace('text', '').strip()
				if line.startswith('integer') or line.startswith('int'):
					dataType = 'INTEGER'
					line = line.replace('integer', '').replace('int', '').strip()
				if line.startswith('boolean') or line.startswith('bool'):
					dataType = 'BOOLEAN'
					line = line.replace('boolean', '').replace('bool', '').strip()
				if not cls.TableProperties[tablename][columnName]['DataType']:
					cls.TableProperties[tablename][columnName]['DataType'] = dataType
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
				if not cls.TableProperties[tablename][columnName]['DefaultValue']:
					cls.TableProperties[tablename][columnName]['DefaultValue'] = defaultValue
				if line.startswith('NOT NULL'):
					line = line.replace("NOT NULL", '').strip()
					notNull = True
				if line.startswith('UNIQUE'):
					line = line.replace("UNIQUE", '').strip()
					unique = True
				cls.TableProperties[tablename][columnName]['NotNull'] 		= notNull
				cls.TableProperties[tablename][columnName]['Unique'] 		= unique
				if line:
					raise ValueError
	@classmethod
	def setOriginalTypesList(cls):
		cls.OriginalEntities = [x[0] for x in DB_ORIGINAL.execute("SELECT Type FROM {}".format(cls.MainTableName)).fetchall()]

	def __init__(self, rawData):
		self._set_template()
		rawData = rawData
		for tableName, valuesList in rawData.items():
			if tableName not in self.DATA.keys(): raise KeyError(f'Таблица <{tableName}> не обнаружена в основной базе данных!')
			if valuesList:

				for queve in valuesList:
					pass
					#print(self.DATA[tableName], queve)
			else:
				pass


	def _set_template(self):
		self.DATA = {}
		self.data = {}
		for tablename, defaults in self.TableProperties.items():
			newGroup = Civ5ValuesGroup(tablename, defaults)
			self.DATA[tablename] = []
			newValues = []
			for key, val in defaults.items():
				name 	 = key
				value  	 = val['DefaultValue']
				newValue = Civ5Value(name, value, val)
				newValues.append(newValue)
			self.DATA[tablename] = newValues

	def __init2__(self, primaryData):
		for key, value in primaryData.items():
			curColumn 	= key
			curValue  	= value

			if key == 'EntityType':
				if not self.__class__.MainTableName: self.set_main_table_name(value)
				if not self.__class__.OriginalTypes: self.select_original_types()
			elif key == 'TableNames':
				if not self.__class__.ValidTables: self.set_valid_tables(value)
			elif key == 'SecondaryTables':
				pass
			else:
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
				if curValue is None: curValue = curAttribs['DefaultValue']
				self.__setattr__(curColumn, Civ5Value(curColumn, curValue, curAttribs))
		self.Original = True if self.Type.value in self.OriginalTypes else False

class BuildingClass(Civ5Entity):
	MainTableName		= 'BuildingClasses'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Building(Civ5Entity):
	MainTableName		= 'Buildings'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Civilization(Civ5Entity):
	MainTableName		= 'Civilizations'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Era(Civ5Entity):
	MainTableName		= 'Eras'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Feature(Civ5Entity):
	MainTableName		= 'Features'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class FakeFeature(Civ5Entity):
	MainTableName		= 'FakeFeatures'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Improvement(Civ5Entity):
	MainTableName		= 'Improvements'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Leader(Civ5Entity):
	MainTableName		= 'Leaders'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Policy(Civ5Entity):
	MainTableName		= 'Policies'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class PolicyBranch(Civ5Entity):
	MainTableName		= 'PolicyBranchTypes'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Resource(Civ5Entity):
	MainTableName		= 'Resources'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Technology(Civ5Entity):
	MainTableName		= 'Technologies'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class UnitClass(Civ5Entity):
	MainTableName		= 'UnitClasses'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)
class Unit(Civ5Entity):
	MainTableName		= 'Units'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, rawData):
		super().__init__(rawData)

classList = ('BuildingClass', 'Building', 	'Civilization', 'Era', 		'Feature', 		'FakeFeature', 	'Improvement',
		  	 'Leader', 		  'Policy', 	'PolicyBranch', 'Resource', 'Technology', 	'UnitClass', 	'Unit')

for table in classList:
	exec("{}.setFamilyTableProperties()".format(table))
	exec("{}.setOriginalTypesList()".format(table))