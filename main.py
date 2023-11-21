from SQL_Module.sql_main import *
from XLS_Module.xls_main import *
from Main_Module.entities import *

tables1 = ('BuildingClasses', 'Buildings', 'Civilizations', 'Eras', 'Features', 'FakeFeatures', 'Improvements',
		  'Leaders', 'Policies', 'PolicyBranchTypes', 'Resources', 'Technologies', 'UnitClasses', 'Units')
tables2 = ('BuildingClass', 'Building', 'Civilization', 'Era', 'Feature', 'FakeFeature', 'Improvement',
		  'Leader', 'Policy', 'PolicyBranch', 'Resource', 'Technology', 'UnitClass', 'Unit')
def parseXLS():
	for table in tables1:
		print('---------- >>>>> Идет обработка таблицы {}'.format(table))
		parse_excel_Civ5_table(table)

def get_table_names(tables):
	for table in tables:
		#exec("print({}.OriginalEntities)".format(table))
		exec("{}('')".format(table))

table = parseCiv5Table('Buildings')


DB_ORIGINAL.close()