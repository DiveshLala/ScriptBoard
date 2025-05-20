class DialogPrompt:

	def __init__(self, prompt, speakers, history, numTurns):
		self.text_prompt = prompt
		self.speakers = speakers
		self.history = history
		self.numTurns = numTurns

	def parseVariables(self, variable_dict):
		
		#update with variables
		if "Variable(" in self.text_prompt:
			for var in variable_dict.keys():
				if variable_dict[var][0] == "Boolean":
					continue
				self.text_prompt = self.text_prompt.replace("Variable(" + var + ")", str(variable_dict[var][1]))

	
	def retrieveInfo(self):
		infoDict = {}
		infoDict["text prompt"] = self.text_prompt
		infoDict["speakers"] = self.speakers
		infoDict["history"] = self.history
		infoDict["turns"] = self.numTurns
		return infoDict