from PyQt5.QtGui import QDrag, QPixmap, QPainter
from PyQt5.QtCore import QMimeData, Qt, QPointF
from PyQt5.QtWidgets import (
	 QApplication,
	 QLabel,
	 QGraphicsPixmapItem,
	 QGraphicsTextItem, 
	 QMenu
)
import window_classes.utility_window as utility
import window_classes.subsequences_window as subsequences
import window_classes.dm_message_window as dm_message_window
from node_connections import *
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

