from SQL_Module.sql_main import *
from XLS_Module.xls_main import *
from Main_Module.entities import *

originTableNames = ('BuildingClasses', 'Buildings', 'Civilizations', 'Eras', 'Features', 'Improvements',
		  			'Leaders', 'Policies', 'PolicyBranchTypes', 'Resources', 'Technologies', 'UnitClasses', 'Units')
tableNamesToClasses = {'BuildingClasses': 	BuildingClass,
					  'Buildings': 			Building,
					  'Civilizations': 		Civilization,
					  'Eras': 				Era,
					  'Features': 			Feature,
					  'FakeFeatures': 		FakeFeature,
					  'Improvements': 		Improvement,
		  			  'Leaders': 			Leader,
					  'Policies':			Policy,
					  'PolicyBranchTypes': 	PolicyBranch,
					  'Resources': 			Resource,
					  'Technologies': 		Technology,
					  'UnitClasses': 		UnitClass,
					  'Units': 				Unit}
tables2 = ('BuildingClass', 'Building', 'Civilization', 'Era', 'Feature', 'FakeFeature', 'Improvement',
		  'Leader', 'Policy', 'PolicyBranch', 'Resource', 'Technology', 'UnitClass', 'Unit')
def parseXLS():
	for table in originTableNames:
		print('---------- >>>>> Идет обработка таблицы {}'.format(table))
		entitiesDict = parseCiv5Table(table)

		for entityName, entityData in entitiesDict.items():
			entityTables 	= list(entityData.keys())
			newClass 		= tableNamesToClasses[entityTables[0]]
			newEntity 		= newClass(entityData)
			#print(entityName, type(newEntity))

def get_table_names(tables):
	for table in tables:
		#exec("print({}.OriginalEntities)".format(table))
		exec("{}('')".format(table))
parseXLS()
#table = parseCiv5Table('Units')


DB_ORIGINAL.close()