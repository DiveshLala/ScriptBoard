from PyQt5.QtWidgets import QMessageBox
import os

class Condition:

	def __init__(self):
		self.targetObject = None
		self.comparator = None
		self.compareValue = None
	
	def updateCondition(self, object, comparator, value, varType):
		self.targetObject = object
		self.targetType = varType
		self.comparator = comparator
		self.compareValue = value

		if self.targetType == "Boolean":
			self.compareValue = checkbool(self.compareValue)
	
	def __eq__(self, otherCondition):
		if not isinstance(otherCondition, Condition):
			return False
		
		return (self.targetObject == otherCondition.targetObject) and (self.comparator == otherCondition.comparator) and (self.compareValue == otherCondition.compareValue)

	def __hash__(self):
		return hash((self.targetObject, self.comparator, self.compareValue))
   
	def displayString(self):
		if ";" in str(self.compareValue) or "；" in str(self.compareValue):
			val = str(self.compareValue).replace(";", " OR ")
			val = val.replace("；", " OR ")
		else:
			val = str(self.compareValue)
		return str(self.targetObject) + " " + str(self.comparator) + " " + val
	
	def retrieveInfo(self):
		infoDict = {}
		infoDict["target"] = self.targetObject
		infoDict["comparator"] = self.comparator
		infoDict["value"] = self.compareValue
		infoDict["type"] = self.targetType
		return infoDict

class MultiCondition:

	def __init__(self):
		self.conditions = []
	
	def addConditions(self, condition):
		if isinstance(condition, Condition):
			self.conditions.append(condition)
		elif isinstance(condition, MultiCondition):
			for c in condition.conditions:
				self.conditions.append(c)
	
	def __eq__(self, otherMultiCondition):
		if not isinstance(otherMultiCondition, MultiCondition):
			return False
		
		otherConds = otherMultiCondition.conditions
		return set(self.conditions) == set(otherConds)
	
	def __hash__(self):
		return hash((self.targetObject, self.comparator, self.compareValue))
	
	def displayString(self):
		valString = ""
		for ind, c in enumerate(self.conditions):
			valString += c.displayString() 
			if ind < len(self.conditions) - 1:
				valString += "\n AND "
		return valString

	def retrieveInfo(self):
		infoDict = {}
		for ind, cond in enumerate(self.conditions):
			d ={}
			d["target"] = cond.targetObject
			d["comparator"] = cond.comparator
			d["value"] = cond.compareValue
			d["type"] = cond.targetType
			infoDict["Condition_" + str(ind)] = d
		return infoDict



def isConditionValid(comparator, value, varType):

		# not an integer
		if comparator != "is anything" and comparator != "true" and comparator != "false" and len(value) == 0:
			msgBox = QMessageBox()
			msgBox.setText("Must enter a value!")
			msgBox.exec()
			return False
		
		# less than zero
		if "character length" in comparator or "word length" in comparator:
			if not value.isnumeric():
				msgBox = QMessageBox()
				msgBox.setText("Must enter a whole number!")
				msgBox.exec()
				return False
			elif int(value) < 0:
				msgBox = QMessageBox()
				msgBox.setText("Number cannot be negative!")
				msgBox.exec()
				return False
		
		# word list does not exist
		if value.startswith("Wordlist("):
			found = False
			filename = value.replace("Wordlist(", "").replace(")", "")
			for x in os.listdir("./word_lists/"):
				if filename == x.replace(".words", ""):
					found = True
					break

			if not found:
				return False
		
		#check comparators
		numeric_comparators = ["=", "<", ">", ">=", "<="]

		if comparator in numeric_comparators:
			if varType == "Int":
				try:
					int(value)
				except:
					msgBox = QMessageBox()
					msgBox.setText("Must enter a valid number!")
					msgBox.exec()
					return False
			elif varType == "Float":
				try:
					float(value)
				except:
					msgBox = QMessageBox()
					msgBox.setText("Must enter a number!")
					msgBox.exec()	
					return False				
		return True


def checkbool(x):
	truth_vals = ["True", "true", "1", True]
	return x in truth_vals