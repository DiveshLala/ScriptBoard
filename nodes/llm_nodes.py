from PyQt5.QtWidgets import QGraphicsTextItem

import window_classes.robot_talk_windows as robot_window
import window_classes.variable_update_window as variable_update
import window_classes.llm_decision_window as llm_decision
from condition import Condition
from node_connections import ConditionOutputJoint
from prompt import DialogPrompt
from nodes.basic_nodes import DialogNode
from nodes.participant_nodes import RobotNode


class RobotLLMNode(RobotNode):

	def __init__(self, id, width, height, parent_scene, llm):
		super(RobotLLMNode, self).__init__(id, width, height, parent_scene)
		self.prompt = DialogPrompt("", "None", "Whole dialog history", 1)
		self.bargeIn = False
		self.gaze = ""
		self.fallback = ""
		self.llm = llm
		if self.llm == "gpt":
			self.modelName = "GPT"
		elif self.llm == "gemini":
			self.modelName = "Gemini"
		else:
			self.modelName = ""
		self.filler = ""
	
	def mouseDoubleClickEvent(self, e):
		environment = [x[0] for x in self.parent_scene.getEnvironment()]
		variables = [x[0] for x in self.parent_scene.getVariables()]
		# wordlists = 
		localModels = self.parent_scene.getLocalModeList()
		dlg = robot_window.TalkLLMWindow(self.prompt, self.labelText, self.bargeIn, environment, variables, self.gaze, self.fallback, self.modelName, self.filler, localModels)
		accept = dlg.exec()
		if accept == 1:
			self.prompt = DialogPrompt(dlg.promptBox.toPlainText(), dlg.participantCombo.currentText(), dlg.contextCombo.currentText(), dlg.numTurns.value())
			self.labelText = dlg.label.text()
			self.gaze = dlg.gazeCombo.currentText()
			self.fallback = dlg.fallbackBox.text()
			self.filler = dlg.getFiller()
			print(self.filler)
			self.modelName = dlg.modelCombo.currentText()
			self.updateDialogLabel()

			#barge in condition
			bargeInConn = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.targetObject == "Barge-in"]
			if dlg.bargeInCheck.isChecked() and len(bargeInConn) == 0:
				nodeXPos = self.sceneBoundingRect().getCoords()[0]
				nodeYPos = self.sceneBoundingRect().getCoords()[1]
				cond = Condition()
				cond.updateCondition("Barge-in", "=", "True", "Boolean")
				self.addConnector(nodeXPos, nodeYPos, self.width/2 - 5, -10, "condition_output", condition=cond)
				self.bargeIn = True
			elif not dlg.bargeInCheck.isChecked() and len(bargeInConn) > 0:
				bargeInConn[0].delete()
				self.connectors.remove(bargeInConn[0])
				self.bargeIn = False
				
			self.parent_scene.setSceneChanged(True)
	
	def updateDialogLabel(self):
		maxLength = 20
		if len(self.labelText.strip()) > 0:
			if self.displayedLabel == None:
				l = QGraphicsTextItem()
				l.setPos(self.pos().x(), self.pos().y() + self.height)
				l.setTextWidth(self.width)
				self.parent_scene.addItem(l)
				self.displayedLabel = l
			if len(self.labelText.strip()) > maxLength:
				self.displayedLabel.setPlainText(self.labelText.strip()[:maxLength] + "...")
			else:
				self.displayedLabel.setPlainText(self.labelText.strip())
		else:
			if self.displayedLabel != None:
				self.parent_scene.removeItem(self.displayedLabel)
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "robot_" + self.llm
		infoDict["label"] = self.labelText
		infoDict["barge-in"] = self.bargeIn
		infoDict["gaze"] = self.gaze
		infoDict["fallback"] = self.fallback
		infoDict["filler"] = self.filler
		infoDict["model name"] = self.modelName
		infoDict["prompt"] = self.prompt.retrieveInfo()
		return infoDict
	
	def setLLM(self, llm, localModels):
		self.llm = llm
		self.set_type("robot_" + llm)
		if llm == "gpt":
			self.modelName = "GPT"
		elif llm == "gemini":
			self.modelName = "Gemini"
		elif llm == "lmstudio":
			if len(localModels) == 0:
				self.modelName = ""
			else:
				self.modelName = localModels[0]


class LLMDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene, llm):
		super(LLMDecisionNode, self).__init__(id, width, height, parent_scene)
		self.parent_scene = parent_scene
		self.prompt = DialogPrompt("", "None", "Whole dialog history", 1)
		self.conditions = []
		self.llm = llm
		if self.llm == "gpt":
			self.modelName = "GPT"
		elif self.llm == "gemini":
			self.modelName = "Gemini"
		else:
			self.modelName = ""
	
	def mouseDoubleClickEvent(self, e):
		localModels = self.parent_scene.getLocalModeList()
		conditions = [c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.comparator != "is other"]
		dlg = llm_decision.LLMDecisionWindow(self.prompt, self.labelText, conditions, self.parent_scene.getVariables(), self.modelName, localModels)
		accept = dlg.exec()
		if accept:

			self.prompt = DialogPrompt(dlg.promptBox.toPlainText(), dlg.participantCombo.currentText(), dlg.contextCombo.currentText(), dlg.numTurns.value())

			new_conditions = dlg.conditions
			
			#add other to new conditions
			if len(new_conditions) > 0:
				else_cond = Condition()
				else_cond.updateCondition("LLM output", "is other", "", dlg.typeCombo.currentText())
				present = [n for n in new_conditions if n.displayString() == else_cond.displayString()]
				if len(present) == 0:
					new_conditions.append(else_cond)

			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			for newCond in new_conditions:
				matchingConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition == newCond]
				if len(matchingConnectors) == 0: #condition is a new one
					conn = self.addConnector(nodeXPos, nodeYPos, self.width + 2, self.height/2 + offset, "condition_output", condition=newCond)
					tempConnectors.append(conn)
				else:	#condition already exists
					conn = matchingConnectors[0]
					conn.relX = self.width + 2
					conn.relY = self.height/2 + offset
					conn.setPosition(nodeXPos + conn.relX, nodeYPos + conn.relY)
					tempConnectors.append(conn)
					conn.adjustConnectorLine()
				offset += 15
			
			# #get rid of all connectors that have been deleted
			removedConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c not in tempConnectors and isinstance(c.condition, Condition)]
			for conn in removedConnectors:
				conn.delete()
						
			inputConnectors = [c for c in self.connectors if not isinstance(c, ConditionOutputJoint)]
			self.connectors = inputConnectors + tempConnectors
			self.labelText = dlg.label.text()
			self.modelName = dlg.modelCombo.currentText()
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = self.llm + "_decision"
		infoDict["label"] = self.labelText
		infoDict["prompt"] = self.prompt.retrieveInfo()
		infoDict["model name"] = self.modelName
		return infoDict

	def setLLM(self, llm, localModels):
		self.llm = llm
		self.set_type(llm + "_decision")
		if llm == "gpt":
			self.modelName = "GPT"
		elif llm == "gemini":
			self.modelName = "Gemini"
		elif llm == "lmstudio":
			if len(localModels) == 0:
				self.modelName = ""
			else:
				self.modelName = localModels[0]
		

class LLMVariableUpdateNode(DialogNode):
	def __init__(self, id, width, height, parent_scene, llm):
		super(LLMVariableUpdateNode, self).__init__(id, width, height, parent_scene)
		self.prompt = DialogPrompt("", "None", "Whole dialog history", 1)
		self.variable = None
		self.llm = llm
		if self.llm == "gpt":
			self.modelName = "GPT"
		elif self.llm == "gemini":
			self.modelName = "Gemini"
		else:
			self.modelName = ""

	def mouseDoubleClickEvent(self, e):
		localModels = self.parent_scene.getLocalModeList()
		dlg = variable_update.LLMVariableUpdateWindow(self.labelText, self.prompt, self.variable, self.parent_scene.getVariables(), self.modelName, localModels)
		accept = dlg.exec()
		if accept:
			self.prompt = DialogPrompt(dlg.promptBox.toPlainText(), dlg.participantCombo.currentText(), dlg.contextCombo.currentText(), dlg.numTurns.value())
			self.variable = dlg.variableCombo.currentText()
			self.labelText = dlg.label.text()
			self.modelName = dlg.modelCombo.currentText()
		self.updateDialogLabel()
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["variable"] = self.variable
		infoDict["type"] = self.llm + "_variable"
		infoDict["prompt"] = self.prompt.retrieveInfo()
		infoDict["label"] = self.labelText
		infoDict["model name"] = self.modelName
		return infoDict

	def setLLM(self, llm, localModels):
		self.llm = llm
		self.set_type(llm + "_variable")
		if llm == "gpt":
			self.modelName = "GPT"
		elif llm == "gemini":
			self.modelName = "Gemini"
		elif llm == "lmstudio":
			if len(localModels) == 0:
				self.modelName = ""
			else:
				self.modelName = localModels[0]
