from PyQt5.QtGui import QDrag, QPixmap, QPainter
from PyQt5.QtCore import QMimeData, Qt, QPointF
from PyQt5.QtWidgets import (
	 QApplication,
	 QLabel,
	 QGraphicsPixmapItem,
	 QGraphicsTextItem, 
	 QMenu
)
import window_classes.human_behavior_window as human_window 
import window_classes.robot_talk_windows as robot_window
import window_classes.variable_update_window as variable_update
import window_classes.variable_decision_window as variable_decision
import window_classes.utility_window as utility
import window_classes.turn_state_decision_window as turn_state_decision
import window_classes.llm_decision_window as llm_decision
import window_classes.subsequences_window as subsequences
import window_classes.dm_message_window as dm_message_window
from condition import Condition, MultiCondition, checkbool
from node_connections import *
from script_processor import get_string_between_brackets
from prompt import DialogPrompt
import os

class Icon(QLabel):
	
	def set_type(self, t):
		self.icon_type = t
	
	def set_pic(self, pic):
		self.setPixmap(pic)
		
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.drag_start_position = event.pos()
	
	def mouseMoveEvent(self, event):
		if not (event.buttons() & Qt.LeftButton):
			return
		if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
			return
		drag = QDrag(self)
		mimedata = QMimeData()
		mimedata.setText(self.text())
		drag.setMimeData(mimedata)
		pixmap = QPixmap(self.size())
		painter = QPainter(pixmap)
		painter.drawPixmap(self.rect(), self.grab())
		painter.end()
		drag.setPixmap(pixmap)
		drag.setHotSpot(event.pos())
		drag.exec_(Qt.CopyAction | Qt.MoveAction)


class DialogNode(QGraphicsPixmapItem):

	def __init__(self, id, width, height, parent_scene):
		super(DialogNode, self).__init__()
		self.id = id
		self.parent_scene = parent_scene
		self.connectors = []
		self.width = width
		self.height = height
		self.connectorLine = None
		self.labelText = ""
		self.displayedLabel = None
		self.icon_type = ""
	
	def set_type(self, t):
		self.icon_type = t
	
	def keyPressEvent(self, e):
		if e.key() == Qt.Key_Delete:
			self.parent_scene.addDeleteNodeToClipboard(self)
			self.deleteFromScene()
			self.parent_scene.setSceneChanged(True)
		if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_C:
			if isinstance(self, StartNode):
				self.parent_scene.copyNode(None)
			else:	
				self.parent_scene.copyNode([self])
	
	def deleteFromScene(self):
		for conn in self.connectors:	
			conn.delete()		
		if self.displayedLabel != None:
			self.parent_scene.removeItem(self.displayedLabel)
		self.parent_scene.removeNode(self)

		
	def addConnector(self, initX, initY, relX, relY, connectorType, condition=None):
		if connectorType == "output":
			connector = OutputJoint(self.parent_scene, initX, initY, relX, relY)
		elif connectorType == "input":
			connector = InputJoint(self.parent_scene, initX, initY, relX, relY)
		elif connectorType == "condition_output":
			connector = ConditionOutputJoint(self.parent_scene, initX, initY, relX, relY, condition)
		self.connectors.append(connector)
		return connector


	def mouseMoveEvent(self, event):
		selectedNodes = [x for x in self.parent_scene.items() if x.isSelected() == True and isinstance(x, DialogNode)]
		if len(selectedNodes) > 1:
			diff_x = self.mapToScene(event.pos()).x() - self.drag_start_position.x()
			diff_y = self.mapToScene(event.pos()).y() - self.drag_start_position.y()
			for n in selectedNodes:
				n.moveNodeToCoordinates(n.drag_start_position.x() + diff_x, n.drag_start_position.y() + diff_y)
		else:
			self.moveNode(event)
		
	def moveNode(self, event):
		self.setPos(event.scenePos().x() - self.width/2, event.scenePos().y() - self.height/2)
		newX = self.sceneBoundingRect().getCoords()[0]
		newY = self.sceneBoundingRect().getCoords()[1]
		for conn in self.connectors:
			conn.setPosition(newX + conn.relX, newY + conn.relY)
			conn.adjustConnectorLine()
		if self.displayedLabel != None:
			self.displayedLabel.setPos(self.pos().x(), self.pos().y() + self.height)
		self.parent_scene.setSceneChanged(True)
	
	def moveNodeToCoordinates(self, x, y):
		self.setPos(x - self.width/2, y - self.height/2)
		newX = self.sceneBoundingRect().getCoords()[0]
		newY = self.sceneBoundingRect().getCoords()[1]
		for conn in self.connectors:
			conn.setPosition(newX + conn.relX, newY + conn.relY)
			conn.adjustConnectorLine()
		if self.displayedLabel != None:
			self.displayedLabel.setPos(self.pos().x(), self.pos().y() + self.height)
		self.parent_scene.setSceneChanged(True)



	def retrieveInfo(self):
		infoDict = {}
		infoDict["id"] = self.id
		infoDict["xpos"] = self.pos().x()
		infoDict["ypos"] = self.pos().y()
		return infoDict

	def mousePressEvent(self, event):
		self.parent_scene.latestClickedNodeID = self.id
		if event.button() == Qt.RightButton:
			self.contextMenu = QMenu()
			startAction = self.contextMenu.addAction("Start")
			startAction.triggered.connect(self.startNode)
			self.show()
		elif event.button() == Qt.LeftButton:
			self.drag_start_position = self.pos()
			if self.parent_scene.multipleSelected:
				selectedNodes = [x for x in self.parent_scene.items() if x.isSelected() == True and isinstance(x, DialogNode)]
				for n in selectedNodes:
					n.drag_start_position = QPointF(n.pos().x(), n.pos().y())
	
	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton:
			super().mouseReleaseEvent(event)
			self.parent_scene.checkForSceneExtension(event.scenePos().x(), event.scenePos().y())
			if self.parent_scene.multipleSelected:
				selectedNodes = [x for x in self.parent_scene.items() if x.isSelected() == True and isinstance(x, DialogNode)]
				nodes = []
				start_positions = []
				after_positions = []
				for n in selectedNodes:
					nodes.append(n)
					start_positions.append(n.drag_start_position)
					after_positions.append(n.pos())
				self.parent_scene.addMoveMultipleToClipboard(nodes, start_positions, after_positions)	
			else:
				self.parent_scene.addMoveToClipboard(self, self.drag_start_position, self.mapToScene(event.pos()))
			pass
		
	def contextMenuEvent(self, event):
		v = self.parent_scene.views()[0]
		sceneP = self.mapToScene(event.pos())
		viewP = v.mapFromScene(sceneP)
		sendMenuEventPos = v.viewport().mapToGlobal(viewP)
		self.contextMenu.exec(sendMenuEventPos)
	
	def startNode(self):
		self.parent_scene.parentWindow.playFromRightClick(self.id)
	
	def updateDialogLabel(self):

		if len(self.labelText.strip()) > 0:
			if self.displayedLabel == None:
				l = QGraphicsTextItem()
				l.setPos(self.pos().x(), self.pos().y() + self.height)
				l.setTextWidth(self.width * 2)
				self.parent_scene.addItem(l)
				self.displayedLabel = l
			self.displayedLabel.setPlainText(self.labelText)
		else:
			if self.displayedLabel != None:
				self.parent_scene.removeItem(self.displayedLabel)
				self.displayedLabel = None
	
	def copyTo(self, obj, scene):
		for k, v in self.__dict__.items():

			#dont update connectors
			if k == "connectors":
				continue

			if k == "id":
				continue

			setattr(obj, k, v)
		obj.parent_scene = scene
		obj.connectorLine = None
		obj.displayedLabel = None
		return obj


class StartNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(StartNode, self).__init__(id, width, height, parent_scene)
		
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "start"
		return infoDict
	


class HumanNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(HumanNode, self).__init__(id, width, height, parent_scene)
	
	def mouseDoubleClickEvent(self, e):
		dlg = human_window.HumanBehaviorWindow([c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint)], self.parent_scene.getVariables(), self.parent_scene.getMainWindow().environment)
		accept = dlg.exec()

		if accept == 1:
			newConditions = dlg.conditions
			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			for newCond in newConditions:
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
			
			#get rid of all connectors that have been deleted
			removedConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c not in tempConnectors and isinstance(c.condition, Condition) and c.condition.targetObject != "Silence time" and c.condition.targetObject != "Timer"]
			for conn in removedConnectors:
				conn.delete()
			removedMultiConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c not in tempConnectors and isinstance(c.condition, MultiCondition)]
			for conn in removedMultiConnectors:
				conn.delete()
			
			#add/remove silence connectors
			silenceConnector = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and isinstance(c.condition, Condition) and c.condition.targetObject == "Silence time"]
			if dlg.silenceCondition != None:
				#already exists, just update
				if len(silenceConnector) > 0:
					silenceConnector[0].condition.compareValue = dlg.silenceCondition.compareValue
					tempConnectors.append(silenceConnector[0])
				else:
					conn = self.addConnector(nodeXPos, nodeYPos, self.width / 2 - 20, self.height + 5, "condition_output", condition=dlg.silenceCondition)
					tempConnectors.append(conn)
			else:
				if len(silenceConnector) > 0:
					silenceConnector[0].delete()
			
			#add/remove timer connectors
			timerConnector = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and isinstance(c.condition, Condition) and c.condition.targetObject == "Timer"]
			if dlg.timerCondition != None:
				#already exists, just update
				if len(timerConnector) > 0:
					timerConnector[0].condition.compareValue = dlg.timerCondition.compareValue
					tempConnectors.append(timerConnector[0])
				else:
					conn = self.addConnector(nodeXPos, nodeYPos, self.width / 2 + 10, self.height + 5, "condition_output", condition=dlg.timerCondition)
					tempConnectors.append(conn)
			else:
				if len(timerConnector) > 0:
					timerConnector[0].delete()

			inputConnectors = [c for c in self.connectors if not isinstance(c, ConditionOutputJoint)]
			self.connectors = inputConnectors + tempConnectors
			self.parent_scene.setSceneChanged(True)
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "human"
		return infoDict
				

class RobotNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(RobotNode, self).__init__(id, width, height, parent_scene)
		self.dialog = ""
		self.tag = ""
		self.emotion = ""
		self.gesture = ""
		self.gaze = ""
		self.bargeIn = False
		self.displayedLabel = None
	
	def mouseDoubleClickEvent(self, e):
		info = [self.dialog, self.tag, self.emotion, self.gesture, self.gaze]
		dlg = robot_window.TalkWindow(info, self.parent_scene.getMainWindow().environment, self.parent_scene.getVariables(), self.bargeIn)
		accept = dlg.exec()
		if accept == 1:
			self.dialog = dlg.textBox.toPlainText()
			self.tag = dlg.tag.text()
			self.emotion = dlg.emotion.text()
			self.gesture = dlg.gesture.text()
			self.gaze = dlg.gazeCombo.currentText()
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
		if len(self.dialog.strip()) > 0:
			if self.displayedLabel == None:
				l = QGraphicsTextItem()
				l.setPos(self.pos().x(), self.pos().y() + self.height)
				l.setTextWidth(self.width)
				self.parent_scene.addItem(l)
				self.displayedLabel = l
			if len(self.dialog.strip()) > maxLength:
				self.displayedLabel.setPlainText(self.dialog.strip()[:maxLength] + "...")
			else:
				self.displayedLabel.setPlainText(self.dialog.strip())
		else:
			if self.displayedLabel != None:
				self.parent_scene.removeItem(self.displayedLabel)	
				self.displayedLabel = None
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "robot"
		infoDict["dialog"] = self.dialog
		infoDict["tag"] = self.tag
		infoDict["emotion"] = self.emotion
		infoDict["gesture"] = self.gesture
		infoDict["gaze"] = self.gaze
		infoDict["barge-in"] = self.bargeIn
		return infoDict


class RobotLLMNode(RobotNode):

	def __init__(self, id, width, height, parent_scene, llm):
		super(RobotLLMNode, self).__init__(id, width, height, parent_scene)
		self.prompt = DialogPrompt("", "None", "Whole dialog history", 1)
		self.bargeIn = False
		self.gaze = ""
		self.fallback = ""
		self.llm = llm
	
	def mouseDoubleClickEvent(self, e):
		dlg = robot_window.TalkLLMWindow(self.prompt, self.labelText, self.bargeIn, [x[0] for x in self.parent_scene.getEnvironment()], [x[0] for x in self.parent_scene.getVariables()], self.gaze, self.fallback)
		accept = dlg.exec()
		if accept == 1:
			self.prompt = DialogPrompt(dlg.promptBox.toPlainText(), dlg.participantCombo.currentText(), dlg.contextCombo.currentText(), dlg.numTurns.value())
			self.labelText = dlg.label.text()
			self.gaze = dlg.gazeCombo.currentText()
			self.fallback = dlg.fallbackBox.text()
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
		infoDict["prompt"] = self.prompt.retrieveInfo()
		return infoDict
	
	def setLLM(self, llm):
		self.llm = llm
		self.set_type("robot_" + llm)

class VariableUpdateNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(VariableUpdateNode, self).__init__(id, width, height, parent_scene)
		self.variableUpdates = []

	def mouseDoubleClickEvent(self, e):
		#no variables
		if len(self.parent_scene.getVariables()) == 0:
			return
		
		dlg = variable_update.VariableUpdateWindow(self.variableUpdates, self.parent_scene.getVariables(), self.parent_scene.getEnvironment())
		accept = dlg.exec()
		if accept == 1:
			self.variableUpdates = dlg.updates
			self.parent_scene.setSceneChanged(True)
			if len(self.variableUpdates) > 0:
				self.labelText = self.variableUpdates[0][0] + "=" + self.variableUpdates[0][1]
				if len(self.variableUpdates) > 1:
					self.labelText += " plus more"
			self.updateDialogLabel()

	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "variable_update"
		variables = {}
		for v in self.variableUpdates:
			variables[v[0]] = v[1]
		infoDict["variables"] = variables
		return infoDict

class VariableDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(VariableDecisionNode, self).__init__(id, width, height, parent_scene)
	

	def mouseDoubleClickEvent(self, e):

		variables = self.parent_scene.getVariables()
		if len(variables) == 0:
			return

		dlg = variable_decision.VariableDecisionWindow([c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.comparator != "is other"], self.parent_scene.getVariables())
		accept = dlg.exec()

		if accept == 1:
			newConditions = dlg.conditions
			
			#add other to new conditions
			if len(newConditions) > 0:
				var_name = get_string_between_brackets(newConditions[0].targetObject)
				for v in self.parent_scene.getVariables():
					if v[0] == var_name:
						var_type = v[1]
						break
				else_cond = Condition()
				if var_type == "Boolean":
					else_cond.updateCondition("Variable(" + var_name + ")", "is", not checkbool(newConditions[0].compareValue), var_type)
				else:
					else_cond.updateCondition("Variable(" + var_name + ")", "is other", "", var_type)
				present = [n for n in newConditions if n.displayString() == else_cond.displayString()]
				if len(present) == 0:
					newConditions.append(else_cond)

			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			for newCond in newConditions:
				matchingConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition == newCond]
				if len(matchingConnectors) == 0: #condition is a new one
					conn = self.addConnector(nodeXPos, nodeYPos, self.width + 2, self.height/2 + offset, "condition_output", condition=newCond)
					print("adding connector", newCond.displayString())
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
			removedConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.displayString() not in [tc.condition.displayString() for tc in tempConnectors]]

			for conn in removedConnectors:
				conn.delete()
						
			if len(tempConnectors) > 0:
				self.labelText = "Decision\n" + get_string_between_brackets(tempConnectors[0].condition.targetObject)
			else:
				self.labelText = ""

			inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
			self.connectors = inputConnectors + tempConnectors
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "variable_decision"
		return infoDict

class LLMDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene, llm):
		super(LLMDecisionNode, self).__init__(id, width, height, parent_scene)
		self.parent_scene = parent_scene
		self.prompt = DialogPrompt("", "None", "Whole dialog history", 1)
		self.conditions = []
		self.llm = llm
	
	def mouseDoubleClickEvent(self, e):
		dlg = llm_decision.LLMDecisionWindow(self.prompt, self.labelText, [c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.comparator != "is other"], self.parent_scene.getVariables())
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
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = self.llm + "_decision"
		infoDict["label"] = self.labelText
		infoDict["prompt"] = self.prompt.retrieveInfo()
		return infoDict

	def setLLM(self, llm):
		self.llm = llm
		self.set_type(llm + "_decision")

class RandomDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(RandomDecisionNode, self).__init__(id, width, height, parent_scene)
		self.num_decisions = 1

	def mouseDoubleClickEvent(self, e):
		dlg = utility.RandomDecisionWindow(self.num_decisions)
		accept = dlg.exec()
		if accept:
			self.num_decisions = int(dlg.numDecisions.value())
			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			oldConnectors = [c for c in self.connectors if isinstance(c, OutputJoint)]

			#if new value is greater, shift the connectors up and add more
			if self.num_decisions > len(oldConnectors):

				for conn in oldConnectors:
					conn.relX = self.width + 2
					conn.relY = self.height/2 + offset
					conn.setPosition(nodeXPos + conn.relX, nodeYPos + conn.relY)
					tempConnectors.append(conn)
					conn.adjustConnectorLine()
					offset += 15
				
				for i in range(self.num_decisions - len(oldConnectors)):
					conn = self.addConnector(nodeXPos, nodeYPos, self.width + 2, self.height/2 + offset, "output")
					tempConnectors.append(conn)
					offset += 15
				
				inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
				self.connectors = inputConnectors + tempConnectors	
			
			#if new value is less, remove extra connectors			
			else:
				for i, conn in enumerate(oldConnectors):
					if self.num_decisions - i > 0:
						conn.relX = self.width + 2
						conn.relY = self.height/2 + offset
						conn.setPosition(nodeXPos + conn.relX, nodeYPos + conn.relY)
						tempConnectors.append(conn)
						conn.adjustConnectorLine()
						offset += 15
					else:
						conn.delete()
				inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
				self.connectors = inputConnectors + tempConnectors	
				
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "random_decision"
		infoDict["number decisions"] = self.num_decisions
		return infoDict

class TurnBasedDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(TurnBasedDecisionNode, self).__init__(id, width, height, parent_scene)
		self.conditions = []

	def mouseDoubleClickEvent(self, e):
		dlg = turn_state_decision.TurnStateDecisionWindow([c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.comparator != "is other"])
		accept = dlg.exec()

		if accept == 1:
			newConditions = dlg.conditions
			
			#add other to new conditions
			if len(newConditions) > 0:
				else_cond = Condition()
				else_cond.updateCondition("Turn state", "is other", "", "String")
				present = [n for n in newConditions if n.displayString() == else_cond.displayString()]
				if len(present) == 0:
					newConditions.append(else_cond)

			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			for newCond in newConditions:
				matchingConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition == newCond]
				if len(matchingConnectors) == 0: #condition is a new one
					conn = self.addConnector(nodeXPos, nodeYPos, self.width + 2, self.height/2 + offset, "condition_output", condition=newCond)
					print("adding connector", newCond.displayString())
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
			removedConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.displayString() not in [tc.condition.displayString() for tc in tempConnectors]]

			for conn in removedConnectors:
				conn.delete()

			inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
			self.connectors = inputConnectors + tempConnectors
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "turn_based_decision"
		return infoDict

class HumanTargetNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(HumanTargetNode, self).__init__(id, width, height, parent_scene)
		self.parent_scene = parent_scene
		self.new_target = None

	def mouseDoubleClickEvent(self, e):
		environment = self.parent_scene.getMainWindow().environment
		dlg = human_window.HumanTargetWindow(self.new_target, environment)
		accept = dlg.exec()
		if accept:
			self.new_target = dlg.chooser.currentText()
			self.labelText = "Target is\n" + self.new_target
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "human_target"
		infoDict["new target"] = self.new_target
		return infoDict

class WaitNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(WaitNode, self).__init__(id, width, height, parent_scene)
		self.wait_time = 0


	def mouseDoubleClickEvent(self, e):
		dlg = utility.WaitWindow(self.wait_time)
		accept = dlg.exec()
		if accept:
			self.wait_time = dlg.waitTime.value()
			self.labelText = "Wait " + str(self.wait_time) + "ms"
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "wait"
		infoDict["wait time"] = self.wait_time
		return infoDict


class ParameterNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(ParameterNode, self).__init__(id, width, height, parent_scene)
		self.wait_time = 0
		self.updates = []

	def mouseDoubleClickEvent(self, e):
		dlg = utility.ParameterWindow(self.updates)
		accept = dlg.exec()
		if accept:
			self.updates = []
			for row in range(dlg.itemModel.rowCount()):
				index = dlg.itemModel.index(row, 0)
				item = dlg.itemModel.data(index)
				self.updates.append(item.split("\t"))

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "parameters"
		parameters = []
		for p in self.updates:
			param_dict = {}
			param_dict["behavior name"] = p[0]
			param_dict["parameter name"] = p[1]
			param_dict["parameter value"] = p[2]
			parameters.append(param_dict)
		infoDict["parameter changes"] = parameters
		return infoDict

class BehaviorStartNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(BehaviorStartNode, self).__init__(id, width, height, parent_scene)
		self.parent_scene = parent_scene
		self.behavior = ""

	def mouseDoubleClickEvent(self, e):
		dlg = utility.BehaviorWindow(self.behavior, self.parent_scene.getMainWindow().isScriptMultiHuman(), "Start")
		accept = dlg.exec()
		if accept:
			self.behavior = dlg.behaviorCombo.currentText()
			self.labelText = "Start " + self.behavior
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)
		
	def updateDialogLabel(self):
		if len(self.labelText.strip()) > 0:
			if self.displayedLabel == None:
				l = QGraphicsTextItem()
				l.setPos(self.pos().x(), self.pos().y() + self.height)
				l.setTextWidth(self.width * 2.5)
				self.parent_scene.addItem(l)
				self.displayedLabel = l
			self.displayedLabel.setPlainText(self.labelText)
		else:
			if self.displayedLabel != None:
				self.parent_scene.removeItem(self.displayedLabel)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "behavior_start"
		infoDict["behavior"] = self.behavior
		return infoDict

class BehaviorStopNode(BehaviorStartNode):
	def __init__(self, id, width, height, parent_scene):
		super(BehaviorStopNode, self).__init__(id, width, height, parent_scene)

	def mouseDoubleClickEvent(self, e):
		dlg = utility.BehaviorWindow(self.behavior, self.parent_scene.getMainWindow().isScriptMultiHuman(), "Stop")
		accept = dlg.exec()
		if accept:
			self.behavior = dlg.behaviorCombo.currentText()
			self.labelText = "Stop " + self.behavior
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "behavior_stop"
		infoDict["behavior"] = self.behavior
		return infoDict

class TimerNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(TimerNode, self).__init__(id, width, height, parent_scene)
		self.timerTime = 1

	def mouseDoubleClickEvent(self, e):
		dlg = utility.TimerWindow(self.timerTime)
		accept = dlg.exec()
		if accept:
			self.timerTime = dlg.timerTime.value()
			self.labelText = "Timer " + str(self.timerTime) + " seconds"
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "timer"
		infoDict["timer time"] = self.timerTime
		return infoDict

class RecordingNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(RecordingNode, self).__init__(id, width, height, parent_scene)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "record"
		return infoDict

class RecordingOffNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(RecordingOffNode, self).__init__(id, width, height, parent_scene)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "record_off"
		return infoDict

class ResetVariableNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(ResetVariableNode, self).__init__(id, width, height, parent_scene)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "reset_variables"
		return infoDict

class AppStartNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(AppStartNode, self).__init__(id, width, height, parent_scene)
		self.appName = ""
		self.parameters = []

	def mouseDoubleClickEvent(self, e):
		dlg = utility.AppStartWindow(self.appName, self.parameters)
		accept = dlg.exec()
		if accept:
			self.appName = dlg.appCombo.currentText()
			self.labelText = self.appName
			self.updateDialogLabel()

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "app_start"
		infoDict["app"] = self.appName
		infoDict["parameters"] = self.parameters
		return infoDict

class TTSParameterNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(TTSParameterNode, self).__init__(id, width, height, parent_scene)
		self.parameters = []

	def mouseDoubleClickEvent(self, e):
		dlg = utility.TTSParameterWindow(self.parameters)
		accept = dlg.exec()
		if accept:
			self.parameters = dlg.params

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "tts_parameters"
		infoDict["parameters"] = self.parameters
		return infoDict


class LLMVariableUpdateNode(DialogNode):
	def __init__(self, id, width, height, parent_scene, llm):
		super(LLMVariableUpdateNode, self).__init__(id, width, height, parent_scene)
		self.prompt = DialogPrompt("", "None", "Whole dialog history", 1)
		self.variable = None
		self.llm = llm

	def mouseDoubleClickEvent(self, e):
		dlg = variable_update.LLMVariableUpdateWindow(self.labelText, self.prompt, self.variable, self.parent_scene.getVariables())
		accept = dlg.exec()
		if accept:
			self.prompt = DialogPrompt(dlg.promptBox.toPlainText(), dlg.participantCombo.currentText(), dlg.contextCombo.currentText(), dlg.numTurns.value())
			self.variable = dlg.variableCombo.currentText()
			self.labelText = dlg.label.text()
		self.updateDialogLabel()
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["variable"] = self.variable
		infoDict["type"] = self.llm + "_variable"
		infoDict["prompt"] = self.prompt.retrieveInfo()
		infoDict["label"] = self.labelText
		return infoDict

	def setLLM(self, llm):
		self.llm = llm
		self.set_type(llm + "_variable")


class PythonFunctionNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(PythonFunctionNode, self).__init__(id, width, height, parent_scene)
		self.functionName = ""
		self.variable = ""

	def mouseDoubleClickEvent(self, e):
		scriptList = [i for i in os.listdir("./functions") if str(i).endswith(".py")]
		dlg = utility.PythonFunctionWindow(scriptList, self.parent_scene.getVariables(), self.functionName, self.variable)
		accept = dlg.exec()
		if accept:
			self.functionName = dlg.scriptCombo.currentText()
			if dlg.variableCheck.isChecked():
				self.variable = dlg.variableCombo.currentText()
			else:
				self.variable = ""
			self.labelText = self.functionName
			self.updateDialogLabel()

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "function"
		infoDict["function name"] = self.functionName
		infoDict["variable"] = self.variable
		return infoDict

class EnterSubsequenceNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(EnterSubsequenceNode, self).__init__(id, width, height, parent_scene)
		self.subseqName = ""

	def mouseDoubleClickEvent(self, e):
		dlg = subsequences.EnterSubsequenceWindow(self.parent_scene.getMainWindow().subsequences, self.subseqName)
		accept = dlg.exec()
		if accept:
			self.subseqName = dlg.subsequenceCombo.currentText()
			self.labelText = self.subseqName
			self.updateDialogLabel()

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "enter_subseq"
		infoDict["subsequence name"] = self.subseqName
		return infoDict

class SendToDMNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(SendToDMNode, self).__init__(id, width, height, parent_scene)
		self.message_dict = {}
		self.message = ""
	

	def mouseDoubleClickEvent(self, e):
		dlg = dm_message_window.DMMessageWindow(self.labelText, self.message_dict)
		accept = dlg.exec()
		if accept:
			self.message = dlg.jsonMessage
			self.message_dict = dlg.get_message_dict()
			self.labelText = dlg.label.text()
			self.updateDialogLabel()
	
	def retrieveInfo(self):
		infodict = super().retrieveInfo()
		infodict["type"] = "send_to_dm"
		infodict["message_dict"] = self.message_dict
		infodict["message"] = self.message
		infodict["label"] = self.labelText
		return infodict

