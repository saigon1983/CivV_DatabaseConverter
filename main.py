from SQL_Module.sql_main import *
from XLS_Module.xls_main import *
from Main_Module.entities import *


for entity in select_all_entities('Buildings').values():
	newEntity = Civ5Entity(entity)


Civ5Entity.DB.close()
DB_ORIGINAL.close()