from bs4 import BeautifulSoup
HEADER  = '<?xml version="1.0" encoding="utf-8"?>\n'    # Заголовок, определяющий кодировку. Нужен в начале каждого xml-файла

def indent(count):
	assert type(count) == int, "Аргумент <count> метода 'indent' должен быть числом!"
	return "\t" * count
def newline(bool = True):
	assert bool in (True, False), "Аргумент <bool> метода 'newline' должен принимать только значения 'True' или 'False'!"
	return "\n" if bool else ""
def comment(someText, indents = 0, newLine = True):
	return f"{indent(indents)}<!-- {someText} -->{newline(newLine)}"
def tagOpen(someTag, indents, newLine = True):
	assert someTag, "Для метода 'tagOpen' не задан тег или тег не является строкой!"
	return f"{indent(indents)}<{someTag}>{newline(newLine)}"
def tagClose(someTag, indents, newLine = True):
	assert someTag, "Для метода 'tagClose' не задан тег или тег не является строкой!"
	return f"{indent(indents)}</{someTag}>{newline(newLine)}"
def placeLine(someTag, someText = "", indents = 0, newLine = True):
	# Возвращает простую строку данных, если текст не задан
	assert someTag, "Для метода 'placeLine' не задан тег или тег не является строкой!"
	return f"{tagOpen(someTag, indents, False)}{str(someText)}{tagClose(someTag, 0, newLine)}" if someText else ""

def placePairs(someDict):
	result = ""
	for key, value in someDict.items():
		someType = type(value)
		if someType in (bool, int, float):
			if someType == bool and value == True:  value = "true"
			if someType == bool and value == False: value = "false"
		result += ' {}="{}"'.format(key, value)
	return result
def makeBody(someDict, indents = 0, startComment = "", finishComment = ""):
	assert type(someDict) == dict, f"Функция 'makeBody' должна получить для обработки словарь или упорядоченный словарь. " \
								   f"Вместо этого получен {type(someDict)}"
	result = comment(startComment, indents) if startComment else ""
	for key, value in someDict.items():
		if " " in key: raise ValueError(f"В имени тега <{key}> не должно быть пробелов!")
		result += placeLine(key, value, indents)
	result += comment(finishComment, indents) if finishComment else ""
	return result
def shiftBody(someBody, indents = 1):
	splitted = someBody.splitlines()
	if indents == 0: return someBody
	result = ""
	for string in splitted:
		if indents > 0: result += "\t" * indents + string + "\n"
		else:
			indentsInString = string.count("\t")
			resultIndents   = max(indentsInString + indents, 0)
			result += "\t" * resultIndents + string[indentsInString:] + "\n"
	return result
def placeEntry(someTag, someBody, indents = 0, someComment = ""):
	result = comment(someComment, indents) if someComment else ""
	result += tagOpen(someTag, indents)
	if type(someBody) == str:		result += shiftBody(someBody, indents-(len(someBody)-len(someBody.lstrip('\t')))+1)
	elif type(someBody) == dict: 	result += makeBody(someBody, indents+1)
	result += tagClose(someTag, indents, True)
	return result if someBody else ""
def placeRow(someBody, indents = 0, someComment = ""):
	return placeEntry("Row", someBody, indents, someComment) if someBody else ""
def placeReplace(someBody, indents = 0, someComment = ""):
	return placeEntry("Replace", someBody, indents, someComment)
def placeDelete(indents = 0, someDict = {}):
	return f"{indent(indents)}<Delete/>\n" if not someDict else f"{indent(indents)}<Delete {placePairs(someDict)} />\n"
def placeUpdate(someCondition = {}, someBody = {}, indents = 0, someComment = ""):
	result = comment(someComment, indents) if someComment else ""
	result += tagOpen("Update", indents, False)
	result += f" <Where{placePairs(someCondition)} />\n"
	result += placeEntry("Set", someBody, indents+1)
	result += tagClose("Update", indents)
	return result
def placeGameData(someBody, header = True, someComment = ""):
	result = comment(someComment, 0) if someComment else ""
	result +=placeEntry("GameData", someBody)
	return HEADER + result if header else result
def placeTableCheck(fileName):
	result = tagOpen("DebugTableCheck", 0)
	result += "\t<Row"
	result += placePairs({"FileName": fileName})
	result += "/>\n"
	result += tagClose("DebugTableCheck", 0)
	return result