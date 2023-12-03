from SQL_Module.sql_main import *
from Main_Module.constants import *
from XML_Module.xml_main import *
import re
class Civ5MajorValue:
	def __init__(self, owner, table, title, value, basic, attrs):
		self.table = table
		self.owner = owner
		self.title = title
		self.value = value
		assert attrs != None, f'Список атрибутов, переданный для значения {self.title} пуст!'
		self.type 		= attrs['DataType']
		self.default 	= attrs['DefaultValue']
		self.reference 	= attrs['References']
		self.autoinc 	= attrs['AutoIncrement']
		self.notnull 	= attrs['NotNull']
		self.unique 	= attrs['Unique']

		self.basic = basic

		if self.value == None and self.title == 'ID':   self.value = self.basic
		if self.value == None and self.default != None: self.value = self.default

		if self.type == 'BOOLEAN':
			if self.value == 'true':  self.value = 1
			if self.value == 'false': self.value = 0
	def likeDefault(self):
		if self.value == 'NULL' and self.default == None: 	return True
		if self.value == 1 and self.default == 'true': 		return True
		if self.value == 0 and self.default == 'false': 	return True
		return self.value == self.default
	def likeOriginal(self):
		if self.value == 'NULL' and self.basic == None: return True
		return self.value == self.basic
	def xml(self):
		title = self.title
		value = self.value
		if self.type == 'BOOLEAN':
			if value == 1: value = 'true'
			if value == 0: value = 'false'
		return placeLine(title, value, 0, False)
	def __str__(self):
		result = f"<{self.owner}> ({self.table}): {self.title} = {self.value} ({self.type}). Default: {self.default}. Original: {self.basic})"
		return result
	def __repr__(self):
		return f"{self.title} = {self.value}"
class Civ5MinorValue:
	def __init__(self, owner, table, array, basic, attrs):
		self.table = table
		self.owner = owner
		self.title = None
		self.value = {}
		assert attrs != None, f'Список атрибутов, переданный для {self.owner} ({self.table}) пуст!'
		for title, value in array.items():
			if value == self.owner:
				self.title = title if not self.title else self.title
			else:
				self.value.update({title: {}})
				self.value[title]['Value'] 		= value
				self.value[title]['Original'] 	= basic[title]
				self.value[title].update(attrs[title])
				if self.value[title]['DataType'] == 'BOOLEAN':
					if self.value[title]['Value'] == 'true':  self.value[title]['Value'] = 1
					if self.value[title]['Value'] == 'false': self.value[title]['Value'] = 0
	def likeOriginal(self):
		for value in self.value.values():
			if value['Value'] != value['Original']:
				return False
		return True
	def xml(self):
		result = {self.title: self.owner, }
		for title, value in self.value.items(): result[title] = value['Value']
		return makeBody(result)
	def __str__(self):
		string = ""
		for title, value in self.value.items(): string += f"{title} = {value['Value']}; "
		return f"<{self.owner}> ({self.table}): {string.strip()}"
	def __repr__(self):
		string = ""
		for title, value in self.value.items(): string += f"{title} = {value['Value']}; "
		return f"({string.strip()})"
class Civ5MajorData:
	def __init__(self, groupName, owner, someData, defaults):
		self.main 		= True
		self.owner		= owner
		self.groupName 	= groupName
		self.groupData 	= []

		for name, value in someData[0].items():
			elementTitle 	= name
			elementValue 	= value
			defaultData		= defaults[name]
			originalValue 	= db_get_value_from_cell(self.groupName, name, 'Type', self.owner)
			newValue = Civ5MajorValue(self.owner, self.groupName, elementTitle, elementValue, originalValue, defaultData)
			self.groupData.append(newValue)
		self.elements = len(self.groupData)
	def __repr__(self):
		return f"Civ5MajorData: <{self.owner} ({self.groupName}, {self.elements} attrs)>"
class Civ5MinorData:
	def __init__(self, groupName, owner, ownerType, someData, defaults, columnNames):
		self.main 		= False
		self.owner		= owner
		self.ownerType	= ownerType
		self.groupName 	= groupName
		self.groupData 	= []
		originalline = db_get_values_from_row(self.groupName, {self.ownerType: self.owner})

		template = {self.ownerType: self.owner,}
		for name in columnNames[1:]: template[name] = None

		for data in someData:
			template 		= data
			originalData	= {}
			defaultData 	= {}
			for d in data.keys():
				originalData.update(db_get_pair_of_values_from_row(self.groupName, data, d))
				defaultData[d] = defaults[d]
			newValue = Civ5MinorValue(self.owner, self.groupName, data, originalData, defaultData)
			self.groupData.append(newValue)
			print(data.keys())
		print("="*30)
	def __repr__(self):
		return f"Civ5MinorData: <{self.owner} ({self.groupName}: {self.groupData})>"
class Civ5ValuesGroup:
	mainTableNames = ('BuildingClasses', 'Buildings', 'Civilizations', 'Eras', 'Features', 'FakeFeatures', 'Improvements',
					  'Leaders', 'Policies', 'PolicyBranchTypes', 'Resources', 'Technologies', 'UnitClasses', 'Units')
	mainTypes = {'BuildingClasses': 	'BuildingClassType',
				 'Buildings': 			'BuildingType',
				 'Civilizations': 		'CivilizationType',
				 'Eras': 				'EraType',
				 'Features': 			'FeatureType',
				 'FakeFeatures': 		'FeatureType',
				 'Improvements': 		'ImprovementType',
				 'Leaders': 			'LeaderType',
				 'Policies': 			'PolicyType',
				 'PolicyBranchTypes': 	'PolicyBranchType',
				 'Resources': 			'ResourceType',
				 'Technologies': 		'TechType',
				 'UnitClasses': 		'UnitClassType',
				 'Units': 				'UnitType'}

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
		self.major = []
		self.minor = []
		for tablename, data in someData.items():
			defaults = self.TableProperties[tablename]
			if tablename in self.SecondaryTablePrefixes.keys():
				newGroup = Civ5MajorData(tablename, self.name, data, defaults)
			else:
				columnNames = tuple(self.TableProperties[tablename].keys())
				ownerType 	= columnNames[0]
				newGroup 	= Civ5MinorData(tablename, self.name, ownerType, data, defaults, columnNames)
			#newGroup = Civ5ValuesGroup(tablename, data, defaults)
			#self.data.append(newGroup)
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