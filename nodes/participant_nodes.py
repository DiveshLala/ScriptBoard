from PyQt5.QtWidgets import QGraphicsTextItem

import window_classes.human_behavior_window as human_window 
import window_classes.robot_talk_windows as robot_window
import window_classes.utility_window as utility
from condition import Condition, MultiCondition
from node_connections import ConditionOutputJoint, OutputJoint
from nodes.basic_nodes import DialogNode


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

