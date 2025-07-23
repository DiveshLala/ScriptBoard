from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
	 QGraphicsScene,
	 QGraphicsItem,
	 QMessageBox,
)
from PyQt5.QtGui import QPixmap
from condition import Condition, MultiCondition
from node_connections import InputJoint, OutputJoint, ConditionOutputJoint, ConnectorLine
from icons import *


class Scene(QGraphicsScene):
	def __init__(self, parentWindow, parent=None):
		super().__init__(parent)
		self.selectionChanged.connect(self.selectionChangeEvent)
		self.state = "IDLE"
		self.multipleSelected = False
		self.minX = 0
		self.maxX = 0
		self.minY = 1000
		self.maxY = 1000
		self.setSceneRect(self.minX, self.minY, (self.maxX - self.minX) + 500, (self.maxY-self.minY) + 500)
		self.parentWindow = parentWindow
		self.sceneChanged = False
		self.latestClickedNodeID = -1
	
	def updateSceneRect(self):
		self.setSceneRect(self.minX - 200, self.minY - 200, (self.maxX - self.minX) + 500, (self.maxY-self.minY) + 500)

	def getItem(self, item):
		for i in self.items():
			if i == item:
				return i
		return None

	def getNodeGivenID(self, id):
		for i in self.items():
			if isinstance(i, DialogNode):
				if i.id == id:
					return i
		return None

	def getInputJointOfNode(self, node):
		for n in self.items():
			if n == node:
				for conn in n.connectors:
					if isinstance(conn, InputJoint):
						return conn
		return None

	def getOwnerOfJoint(self, joint):
		return self.getMainWindow().getOwnerOfJoint(joint)

	def dropEvent(self, event):
		drop_pos = event.scenePos()
		
		if event.source().icon_type == "start":

			if self.getStartNode() == None:
				pixmap = QPixmap("pics/start.png")
				node = StartNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
				node.addConnector(drop_pos.x(), drop_pos.y(), node.width + 2, node.height/2, "output")
			else:
				msgBox = QMessageBox()
				msgBox.setWindowTitle("Multiple start nodes!")
				msgBox.setText("Your script can only contain one start node!")
				msgBox.exec()
				return
					
		elif event.source().icon_type == "human":
			pixmap = QPixmap("pics/human.png")
			node = HumanNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")
		
		elif event.source().icon_type == "variable_decision":
			pixmap = QPixmap("pics/variable_decision.png")
			node = VariableDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")
		
		elif event.source().icon_type == "gpt_decision":
			pixmap = QPixmap("pics/gpt_decision.png")
			node = GPTDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")
		
		elif event.source().icon_type == "gemini_decision":
			pixmap = QPixmap("pics/gemini_decision.png")
			node = GeminiDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")
		
		elif event.source().icon_type == "lmstudio_decision":
			pixmap = QPixmap("pics/lmstudio_decision.png")
			node = LMStudioDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")

		elif event.source().icon_type == "random_decision":
			pixmap = QPixmap("pics/random_decision.png")
			node = RandomDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")
		
		elif event.source().icon_type == "turn_based_decision":
			pixmap = QPixmap("pics/turn_based_decision.png")
			node = TurnBasedDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
			node.addConnector(drop_pos.x(), drop_pos.y(), -12, node.height/2, "input")
		else:
			node, pixmap = self.createInputOutputNode(event.source().icon_type, drop_pos.x(), drop_pos.y())
		
		node.set_type(event.source().icon_type)

		self.placeNode(node, pixmap, drop_pos.x(), drop_pos.y(), sceneCheck=True)
		self.parentWindow.incrementID()
		self.setSceneChanged(True)
		self.addNewNodeToClipboard(node)
	

	def createInputOutputNode(self, icon_type, x, y):
		pixmap = QPixmap("pics/" + icon_type + ".png")
		if icon_type == "robot":
			node = RobotNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "robot_gpt":
			node = RobotGPTNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "robot_gemini":
			node = RobotGeminiNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "robot_lmstudio":
			node = RobotLMStudioNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "human_target":
			node = HumanTargetNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "variable_update":
			node = VariableUpdateNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "wait":
			node = WaitNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "parameters":
			node = ParameterNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "behavior_start":
			node = BehaviorStartNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "behavior_stop":
			node = BehaviorStopNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "timer":
			node = TimerNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "record":
			node = RecordingNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "record_off":
			node = RecordingOffNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "app_start":
			node = AppStartNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "tts_parameters":
			node = TTSParameterNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "gpt_variable":
			node = GPTVariableUpdateNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "gemini_variable":
			node = GeminiVariableUpdateNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "lmstudio_variable":
			node = LMStudioVariableUpdateNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "python_function":
			node = PythonFunctionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "enter_subseq":
			node = EnterSubsequenceNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "reset_variables":
			node = ResetVariableNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
		elif icon_type == "send_to_dm":
			node = SendToDMNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)

		#inital input connector
		node.addConnector(x, y, -12, node.height/2, "input")

		#inital output connector
		node.addConnector(x, y, node.width + 2, node.height/2, "output")

		return node, pixmap


	def placeNode(self, node, pixmap, x, y, sceneCheck=True):

		node.setPixmap(pixmap)
		self.addItem(node)

		node.setPos(x, y)
		node.setFlag(QGraphicsItem.ItemIsMovable)
		node.setFlag(QGraphicsItem.ItemIsSelectable)
		node.setFlag(QGraphicsItem.ItemIsFocusable)

		if sceneCheck:
			self.checkForSceneExtension(x, y)
	
	def checkForSceneExtension(self, x, y):
		if x > self.maxX:
			self.maxX = x
		if x < self.minX:
			self.minX = x
		if y > self.maxY:
			self.maxY = y
		if y < self.minY:
			self.minY = y
		self.updateSceneRect()

	
	def keyPressEvent(self, event):
		if self.multipleSelected:
			if event.key() == Qt.Key_Delete:
				selectedNodes = [x for x in self.items() if x.isSelected() == True and isinstance(x, DialogNode)]
				self.addDeleteMultipleNodesToClipboard(selectedNodes)
				for n in selectedNodes:
					n.deleteFromScene()
				
			if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
				selectedNodes = [x for x in self.items() if x.isSelected() == True and isinstance(x, DialogNode) and not isinstance(x, StartNode)]
				selectedConnectorLines = [x for x in self.items() if x.isSelected() == True and isinstance(x, ConnectorLine)]
				relevantConnections = [l for l in selectedConnectorLines if self.getOwnerOfJoint(l.inputJoint) in selectedNodes and self.getOwnerOfJoint(l.outputJoint) in selectedNodes]
				self.copyNode(selectedNodes + relevantConnections)
		else:
			if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V and self.getMainWindow().getCopiedNodes() != None:
				self.pasteNode()
			elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
				self.undoAction()
			super(Scene, self).keyPressEvent(event)
	
	def undoAction(self):
		self.getMainWindow().undoLatestAction(self)
	
	def wheelEvent(self,event):
		if event.delta() < 0:
			self.parentWindow.zoomOut()
		else:
			self.parentWindow.zoomIn()
			
	def dragMoveEvent(self, e):
		e.acceptProposedAction()

	def removeNode(self, node):
		self.removeItem(node)

	def mouseReleaseEvent(self, event):
		super(Scene, self).mouseReleaseEvent(event)
		selectedNodes = [x for x in self.items() if x.isSelected() == True and isinstance(x, DialogNode)]
		selectedNonNodes = [x for x in self.items() if x.isSelected() == True and not isinstance(x, DialogNode) and not isinstance(x, ConnectorLine)]
		if len(selectedNodes) > 1:
			self.multipleSelected = True
			[n.setSelected(False) for n in selectedNonNodes]
		else:
			if len(selectedNodes) == 1:
				[n.setSelected(False) for n in selectedNonNodes]
			self.multipleSelected = False

	
	def selectionChangeEvent(self):
		for item in self.items():
			if isinstance(item, ConnectorLine):
				if item.isSelected():
					item.updateColor("red")
				else:
					item.updateColor("black")
	
	def findNodeBelongingToConnector(self, conn):
		for item in self.items():
			if isinstance(item, DialogNode):
				if conn in item.connectors:
					return item
		return None

	def getVariables(self):
		return self.parentWindow.getMainWindow().variables
	
	def getEnvironment(self):
		return self.parentWindow.getMainWindow().environment

	def doesNodeUseVariable(self, name):
		for n in self.items():
			if isinstance(n, ConditionOutputJoint):
				condition = n.condition
				if isinstance(condition, Condition):
					if condition.targetObject == "Variable(" + name + ")":
						return True
				elif isinstance(condition, MultiCondition):
					for c in condition.conditions:
						if c.targetObject == "Variable(" + name + ")":
							return True
			elif isinstance(n, VariableUpdateNode):
				if name in [x[0] for x in n.variableUpdates]:
					return True
				if any("Variable(" + name + ")" in s for s in [x[1] for x in n.variableUpdates]):
					return True
			elif isinstance(n, RobotNode):
				if "Variable(" + name + ")" in n.dialog:
					return True
			elif isinstance(n, GPTVariableUpdateNode) or isinstance(n, GeminiVariableUpdateNode):
				if n.variable == name:
					return True
		return False

	def updateVariableNameForScript(self, oldName, newName):
		for n in self.items():
			if isinstance(n, ConditionOutputJoint):
				condition = n.condition
				if isinstance(condition, Condition):
					if condition.targetObject == "Variable(" + oldName + ")":
						condition.targetObject = "Variable(" + newName + ")"
				elif isinstance(condition, MultiCondition):
					for c in condition.conditions:
						if c.targetObject == "Variable(" + oldName + ")":
							c.targetObject = "Variable(" + newName + ")"
			elif isinstance(n, VariableUpdateNode):
				#variable used as target
				match = [ind for ind, x in enumerate(n.variableUpdates) if x[0] == oldName]
				if len(match) > 0:
					index = match[0]
					n.variableUpdates[index][0] = newName
				
				#variable used for calculation
				matches = [ind for ind, x in enumerate(n.variableUpdates) if "Variable(" + oldName + ")" in x[1]]
				for i in matches:
					n.variableUpdates[i][1] = n.variableUpdates[i][1].replace(oldName, newName)
			elif isinstance(n, RobotNode):
				n.dialog = n.dialog.replace("Variable(" + oldName + ")", "Variable(" + newName + ")")
			elif isinstance(n, GPTVariableUpdateNode) or isinstance(n, GeminiVariableUpdateNode):
				if n.variable == oldName:
					n.variable = newName
	
	def removeVariableFromScript(self, varName):
		for n in self.items():
			if isinstance(n, ConditionOutputJoint):
				condition = n.condition
				if isinstance(condition, Condition):
					if condition.targetObject == varName:
						if n.connectorLine != None:
							n.connectorLine.remove()
						node = self.findNodeBelongingToConnector(n)
						node.connectors.remove(n)
						self.removeItem(n)
				elif isinstance(condition, MultiCondition):
					for c in condition.conditions:
						if c.targetObject == varName:
							condition.conditions.remove(c)
					#change to a single condition
					if len(condition.conditions) == 1:
						n.condition = condition.conditions[0]
			elif isinstance(n, VariableUpdateNode):
				match = [x for x in n.variableUpdates if x[0] == varName]
				if len(match) > 0:
					n.variableUpdates.remove(match[0])
				matches = [x for x in n.variableUpdates if "Variable(" + varName + ")" in x[1]]
				for m in matches:
					n.variableUpdates.remove(m)
			elif isinstance(n, RobotNode):
				n.dialog = n.dialog.replace("Variable(" + varName + ")", "")
				n.labelText = ""
				n.updateDialogLabel()
			elif isinstance(n, GPTVariableUpdateNode) or isinstance(n, GeminiVariableUpdateNode):
				if n.variable == varName:
					n.variable = None

	def doesScriptUseLLM(self, llm):
		for n in self.items():
			if isinstance(n, DialogNode):
				if n.icon_type == "robot_" + llm:
					return True
				elif n.icon_type == llm + "_variable":
					return True
				elif n.icon_type == llm + "_decision":
					return True
		return False

	
	def getStartNode(self):
		for n in self.items():
			if isinstance(n, StartNode):
				return n.id
		return None

	def setSceneChanged(self, b):
		self.sceneChanged = b
	
	def getMainWindow(self):
		return self.parentWindow.getMainWindow()
	
	def disableAllNodes(self):
		[n.setEnabled(False) for n in self.items()]
	
	def enableAllNodes(self):
		[n.setEnabled(True) for n in self.items()]
	
	def copyNode(self, nodes):
		self.getMainWindow().setCopiedNodes(nodes, self)
	
	def pasteNode(self, mouseX=None, mouseY=None):

		pastedNodes = []

		if self.getMainWindow().getCopiedNodes() != None:
			copiedNodes = [n for n in self.getMainWindow().getCopiedNodes() if isinstance(n, DialogNode)]
			copiedLines = [n for n in self.getMainWindow().getCopiedNodes() if isinstance(n, ConnectorLine)]

			newConnectorLines = []
			#map lines to relevant nodes
			for l in copiedLines:
				inputNodeInd = copiedNodes.index(self.getOwnerOfJoint(l.inputJoint))
				outputNodeInd = copiedNodes.index(self.getOwnerOfJoint(l.outputJoint))
				outputJointInd = [c for c in self.getOwnerOfJoint(l.outputJoint).connectors if isinstance(c, OutputJoint)].index(l.outputJoint)
				newConnectorLines.append([l, inputNodeInd, outputNodeInd, outputJointInd])

			#nodes are translated to this position
			if mouseX != None and mouseY != None:
				anchorX = mouseX
				anchorY = mouseY
			elif self == self.getMainWindow().getCopiedSource():
				anchorX = copiedNodes[0].sceneBoundingRect().getCoords()[0] + 20
				anchorY = copiedNodes[0].sceneBoundingRect().getCoords()[1] + 20
			else:
				anchorX = self.parentWindow.getCenterOfScene().x()
				anchorY = self.parentWindow.getCenterOfScene().y()
							
			for n in copiedNodes:
				new_x = anchorX + (n.sceneBoundingRect().getCoords()[0] - copiedNodes[0].sceneBoundingRect().getCoords()[0])
				new_y = anchorY + (n.sceneBoundingRect().getCoords()[1] - copiedNodes[0].sceneBoundingRect().getCoords()[1])

				if n.icon_type == "human":
					pixmap = QPixmap("pics/human.png")
					newNode = HumanNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)

					#inital input connector
					newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")

					#conditions and connectors
					offset = -30
					for c in n.connectors:
						if isinstance(c, ConditionOutputJoint):
							#ignore silence connector for now
							if not isinstance(c.condition, MultiCondition) and c.condition.targetObject == "Silence time":
								continue
							elif not isinstance(c.condition, MultiCondition) and c.condition.targetObject == "Timer":
								continue
							else:
								newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "condition_output", condition=c.condition)
								offset += 15
				
				elif n.icon_type == "variable_decision":
					#conditions and connectors
					pixmap = QPixmap("pics/variable_decision.png")
					newNode = VariableDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
					offset = -30
					for c in n.connectors:
						if isinstance(c, ConditionOutputJoint):
							newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "condition_output", condition=c.condition)
							offset += 15	
						elif isinstance(c, InputJoint):
							newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")

				elif n.icon_type == "gpt_decision":
					#conditions and connectors
					pixmap = QPixmap("pics/gpt_decision.png")
					newNode = GPTDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
					offset = -30
					for c in n.connectors:
						if isinstance(c, ConditionOutputJoint):
							newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "condition_output", condition=c.condition)
							offset += 15	
						elif isinstance(c, InputJoint):
							newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")

				elif n.icon_type == "gemini_decision":
					#conditions and connectors
					pixmap = QPixmap("pics/gemini_decision.png")
					newNode = GeminiDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
					offset = -30
					for c in n.connectors:
						if isinstance(c, ConditionOutputJoint):
							newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "condition_output", condition=c.condition)
							offset += 15	
						elif isinstance(c, InputJoint):
							newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")

				elif n.icon_type == "lmstudio_decision":
					#conditions and connectors
					pixmap = QPixmap("pics/lmstudio_decision.png")
					newNode = LMStudioDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
					offset = -30
					for c in n.connectors:
						if isinstance(c, ConditionOutputJoint):
							newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "condition_output", condition=c.condition)
							offset += 15	
						elif isinstance(c, InputJoint):
							newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")	

				elif n.icon_type == "random_decision":
					#conditions and connectors
					pixmap = QPixmap("pics/random_decision.png")
					newNode = RandomDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
					offset = -30
					for c in n.connectors:
						if isinstance(c, OutputJoint):
							newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "output")
							offset += 15	
						elif isinstance(c, InputJoint):
							newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")	

				elif n.icon_type == "turn_based_decision":
					#conditions and connectors
					pixmap = QPixmap("pics/turn_based_decision.png")
					newNode = TurnBasedDecisionNode(self.parentWindow.getMainWindow().idctr, pixmap.width(), pixmap.height(), self)
					offset = -30
					for c in n.connectors:
						if isinstance(c, ConditionOutputJoint):
							newNode.addConnector(new_x, new_y, newNode.width + 2, newNode.height/2 + offset, "condition_output", condition=c.condition)
							offset += 15	
						elif isinstance(c, InputJoint):
							newNode.addConnector(new_x, new_y, -12, newNode.height/2, "input")			
				else:
					newNode, pixmap = self.createInputOutputNode(n.icon_type, new_x, new_y)

				newNode = n.copyTo(newNode, self)
				self.placeNode(newNode, pixmap, new_x, new_y, sceneCheck=True)
				newNode.updateDialogLabel()
				self.parentWindow.incrementID()
				self.setSceneChanged(True)
				pastedNodes.append(newNode)
			
				#add barge in connector for robot node
				if (isinstance(n, RobotNode) or isinstance(n, RobotGPTNode)) and n.bargeIn:
					nodeXPos = newNode.pos().x()
					nodeYPos =  newNode.pos().y()
					cond = Condition()
					cond.updateCondition("Barge-in", "=", "True", "Boolean")
					newNode.addConnector(nodeXPos, nodeYPos, newNode.width/2 - 5, -10, "condition_output", condition=cond)
					newNode.bargeIn = True
				
				#add silence connector for human node
				if isinstance(n, HumanNode):
					hasSilence = [c for c in n.connectors if isinstance(c, ConditionOutputJoint) if not isinstance(c.condition, MultiCondition) and c.condition.targetObject == "Silence time"]
					if len(hasSilence) > 0:
						newNode.addConnector(newNode.pos().x(), newNode.pos().y(), newNode.width / 2 - 20, newNode.height + 5, "condition_output", condition=hasSilence[0].condition)
				#add timer connector for human node
				if isinstance(n, HumanNode):
					hasTimer = [c for c in n.connectors if isinstance(c, ConditionOutputJoint) if not isinstance(c.condition, MultiCondition) and c.condition.targetObject == "Timer"]
					if len(hasTimer) > 0:
						newNode.addConnector(newNode.pos().x(), newNode.pos().y(), newNode.width / 2 + 10, newNode.height + 5, "condition_output", condition=hasTimer[0].condition)
			
			pastedLines = []
			#add connector lines:
			for line in newConnectorLines:
				inputNode = pastedNodes[line[1]]
				outputNode = pastedNodes[line[2]]
				inputJoint = [c for c in inputNode.connectors if isinstance(c, InputJoint)][0]
				outputJoint = [c for c in outputNode.connectors if isinstance(c, OutputJoint)][line[3]]
				connectorLine = ConnectorLine(self, outputJoint, inputJoint)
				connectorLine.setLine(outputJoint.pos().x() + 5, outputJoint.pos().y() + 5, inputJoint.pos().x() + 5, inputJoint.pos().y() + 5)
				inputJoint.addConnectorLine(connectorLine)
				self.addItem(connectorLine)
				inputJoint.addOutputJoint(outputJoint)
				outputJoint.connectedInputJoint = inputJoint
				outputJoint.connectorLine = connectorLine
				pastedLines.append(connectorLine)
			
			self.addMultipleNodesToClipboard(pastedNodes, [n.pos() for n in pastedNodes])

			#ensure that the newly pasted nodes are selected
			for n in pastedNodes:
				n.setSelected(True)
				n.drag_start_position = n.pos()
			if len(pastedNodes) == 1:
				self.multipleSelected = False
			else:
				self.multipleSelected = True
	
	def addNewNodeToClipboard(self, node):
		self.getMainWindow().addActionToClipboard(createAction(self, "new node", node, node.pos(), node.pos()))
	
	def addMultipleNodesToClipboard(self, nodes, positions):
		self.getMainWindow().addActionToClipboard(createAction(self, "new multiple nodes", nodes, positions, positions))
		
	def addNewConnectorLineToClipboard(self, line):
		self.getMainWindow().addActionToClipboard(createAction(self, "new connector line", line, None, None))
	
	def addMoveToClipboard(self, node, before, after):
		self.getMainWindow().addActionToClipboard(createAction(self, "move node", node, before, after))
	
	def addMoveMultipleToClipboard(self, nodes, before_positions, after_positions):
		self.getMainWindow().addActionToClipboard(createAction(self, "move multiple nodes", nodes, before_positions, after_positions))

	def addDeleteNodeToClipboard(self, node):
		self.getMainWindow().addActionToClipboard(createAction(self, "delete node", node, None, None))
	
	def addDeleteConnectorLineToClipboard(self, line, input, output):
		self.getMainWindow().addActionToClipboard(createAction(self, "delete connector line", line, input, output))
	
	def addDeleteMultipleNodesToClipboard(self, nodes):
		self.getMainWindow().addActionToClipboard(createAction(self, "delete multiple nodes", nodes, None, None))
	


def createAction(scene, type, object, pos_before, pos_after):
	action_info = {}
	action_info["scene"] = scene
	action_info["type"] = type
	action_info["object"] = object
	action_info["position"] = [pos_before, pos_after]
	return action_info