from SQL_Module.sql_main import *
from Main_Module.constants import *
from XML_Module.xml_main import *
import re

class Civ5Value:
	def __init__(self, name, value, attributes):
		self.name  		= name
		self.value 		= value
		assert attributes != None, f'Список атрибутов, переданный для значения {self.name} пуст!'
		self.type 		= attributes['DataType']
		self.default 	= attributes['DefaultValue']
		self.reference 	= attributes['References']
		self.autoinc 	= attributes['AutoIncrement']
		self.notnull 	= attributes['NotNull']
		self.unique 	= attributes['Unique']

		if self.value == None and self.default != None: self.value = self.default
	def __str__(self):
		return f'{self.name}: {self.value} ({self.type}, {self.notDefault()})'
	def __repr__(self):
		return f'{self.name}: {self.value} ({self.type}, {self.notDefault()})'
	def notDefault(self):
		return not (self.value == self.default)
	def xml(self):
		return placeLine(self.name, self.value, 0, False)

class Civ5ValuesGroup:
	def __init__(self, groupName, someData, defaults):
		self.name = groupName
		self.data = []

		print("="*20)
		print(self.name)

		for data in someData:
			queue = []
			requests = []
			for name, value in data.items():
				sqlName  = name
				sqlValue = value
				if name == 'Unique':
					print("!!!!!")
					sqlName = f"'{name}'"
				requests.append(f"{sqlName} = '{sqlValue}' ")

				queue.append(Civ5Value(name, value, defaults[name]))
			request = f"SELECT * FROM {self.name} WHERE {'AND '.join(requests[:-1])} "
			sqlValue = DB_ORIGINAL.execute(request)
			if self.name.startswith("Resource"):
				print(request)
				print(sqlValue.fetchone())
				print(queue)
			print('*'*20)
			self.data.append(tuple(queue))
		print("="*20)
		self.elements = len(self.data)
	def xml(self, tag = "Row", short = True):
		result = ""
		for queue in self.data:
			body = ""
			for element in queue:
				subbody = ""
				if element.value != None:
					subbody += element.xml()
					subbody += "\n"
					if short and not element.notDefault(): subbody = ""
					body += subbody
			result += getCommand(tag)(body)
		return result
	def xmlGroup(self, tag = "Row", short = True):
		result = self.xml(tag, short)
		return placeEntry(self.name, result)
	def __repr__(self):
		return f"<Group {self.name} (Elements: {self.elements})>"

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

			start  	= SQLDBFILE.find(f'CREATE TABLE IF NOT EXISTS "{tablename}" (')
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

	def __init__(self, thisName, someData):
		self.name = thisName
		self.data = []
		for tablename, data in someData.items():
			defaults = self.TableProperties[tablename]
			newGroup = Civ5ValuesGroup(tablename, data, defaults)
			self.data.append(newGroup)
		self.real = True if self.name in self.OriginalEntities else False

	def xml(self):
		result = ""
		body = ""
		for group in self.data:
			body += group.xmlGroup()
		result = placeGameData(body)
		return result
class BuildingClass(Civ5Entity):
	MainTableName		= 'BuildingClasses'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Building(Civ5Entity):
	MainTableName		= 'Buildings'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Civilization(Civ5Entity):
	MainTableName		= 'Civilizations'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Era(Civ5Entity):
	MainTableName		= 'Eras'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Feature(Civ5Entity):
	MainTableName		= 'Features'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class FakeFeature(Civ5Entity):
	MainTableName		= 'FakeFeatures'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Improvement(Civ5Entity):
	MainTableName		= 'Improvements'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Leader(Civ5Entity):
	MainTableName		= 'Leaders'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Policy(Civ5Entity):
	MainTableName		= 'Policies'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class PolicyBranch(Civ5Entity):
	MainTableName		= 'PolicyBranchTypes'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Resource(Civ5Entity):
	MainTableName		= 'Resources'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Technology(Civ5Entity):
	MainTableName		= 'Technologies'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class UnitClass(Civ5Entity):
	MainTableName		= 'UnitClasses'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)
class Unit(Civ5Entity):
	MainTableName		= 'Units'
	OriginalEntities	= []
	TableProperties 	= {}
	def __init__(self, thisName, someData):
		super().__init__(thisName, someData)

classList = ('BuildingClass', 'Building', 	'Civilization', 'Era', 		'Feature', 		'FakeFeature', 	'Improvement',
		  	 'Leader', 		  'Policy', 	'PolicyBranch', 'Resource', 'Technology', 	'UnitClass', 	'Unit')

for table in classList:
	exec(f"{table}.setFamilyTableProperties()")
	exec(f"{table}.setOriginalTypesList()")