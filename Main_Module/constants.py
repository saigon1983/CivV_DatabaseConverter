import sqlite3

DB_ORIGINAL = sqlite3.connect('Original/Database/Civ5DebugDatabase.db')
DB_MODIFIED = None

with open("Original/Database/Civ5DebugDatabase.sql", 'r') as sql:
	SQLDBFILE = sql.read()
