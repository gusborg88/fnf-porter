"""
A class full of tools needed for mod conversion.
"""

import time
from psychtobase.src import Constants

def getRuntime(start:float) -> float:
	return start - time.time()

def character(name:str) -> str:
	"""
	Some characters might have changed names in the Base Game,
	this will help you convert their names.

	Args:
		name (str): Name of the character.
	"""

	return Constants.CHARACTERS.get(name, name)

def stage(name:str) -> str:
	"""
	Some stages might have changed names in the Base Game,
	this will help you convert their names.

	Args:
		name (str): Name of the stage.
	"""

	return Constants.STAGES.get(name, name)

def timeChange(timeStamp:float, bpm:float, timeSignatureNum:int, timeSignatureDen:int, beatTime:int, beatTuplets:list) -> dict:
	"""
	Function created for faster creation of song time changes.
	"""
	return {
		"t": timeStamp,
		"b": beatTime,
		"bpm": bpm,
		"n": timeSignatureNum,
		"d": timeSignatureDen,
		"bt": beatTuplets
	}

def note(time:str, data:int, length:float) -> dict:
	"""
	Function created for faster creation of note data.
	"""
	return {
		"t": time,
		"d": data,
		"l": length
	}

def event(time:float, event:str, values:dict) -> dict:
	"""
	Function created for faster creation of events.
	"""
	return {
		"t": time,
		"e": event,
		"v": values
	}

def focusCamera(time:float, char:bool):
	"""
	Function created for faster creation of camera change events.
	"""
	return event(time, "FocusCamera", {"char": "0" if char else "1"})

def coolText(text:str) -> str:
	length = max(30, len(text) + 5)
	length += len(text) % 2

	text = " " * ((length - len(text)) // 2) + text
	return "\n" + "=" * length + f"\n{text}\n" + "=" * length