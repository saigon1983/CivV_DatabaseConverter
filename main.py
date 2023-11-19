from SQL_Module.sql_main import *
from XLS_Module.xls_main import *
from Main_Module.entities import *

tables = ('BuildingClasses', 'Buildings', 'Civilizations', 'Eras', 'Features', 'Improvements',
		  'Leaders', 'Policies', 'PolicyBranchTypes', 'Resources', 'Technologies', 'UnitClasses', 'Units')
def parseXLS():
	for table in tables:
		print('---------- >>>>> Идет обработка таблицы {}'.format(table))
		for entity in select_all_entities(table).values():
			if table == 'BuildingClasses':
				newEntity = BuildingClass(entity)
			if table == 'Buildings':
				newEntity = Building(entity)
			if table == 'Civilizations':
				newEntity = Civilization(entity)
			if table == 'Eras':
				newEntity = Era(entity)
			if table == 'Features':
				newEntity = Feature(entity)
			if table == 'Improvements':
				newEntity = Improvement(entity)
			if table == 'Leaders':
				newEntity = Leader(entity)
			if table == 'Policies':
				newEntity = Policy(entity)
			if table == 'PolicyBranchTypes':
				newEntity = PolicyBranch(entity)
			if table == 'Resources':
				newEntity = Resource(entity)
			if table == 'Technologies':
				newEntity = Technology(entity)
			if table == 'UnitClasses':
				newEntity = UnitClass(entity)
			if table == 'Units':
				newEntity = Unit(entity)

for table in tables:
	print('---------- >>>>> Идет обработка таблицы {}'.format(table))
	parse_excel_Civ5_table(table)



Civ5Entity.DB.close()
DB_ORIGINAL.close()