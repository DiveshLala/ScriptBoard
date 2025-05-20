from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
	 QGraphicsItem,
	 QGraphicsEllipseItem,
	 QGraphicsLineItem,
	 QGraphicsTextItem, 
)

black_brush = QBrush(Qt.black)
red_brush = QBrush(Qt.red)

class ConnectorJoint(QGraphicsEllipseItem):

	def __init__(self, parent_scene, initX, initY, relX, relY):
		super(ConnectorJoint, self).__init__()

		self.setRect(0, 0, 10, 10)
		brush = QBrush(Qt.black)
		self.setBrush(brush)
		parent_scene.addItem(self)
		self.parent_scene = parent_scene
		self.setPos(initX + relX, initY + relY) 
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setFlag(QGraphicsItem.ItemIsFocusable)
		self.relX = relX
		self.relY = relY
		self.tempLine = None
	
	def setPosition(self, x, y):
		self.setPos(x, y)
	
	def retrieveInfo(self):
		infoDict = {}
		infoDict["relX"] = self.relX
		infoDict["relY"] = self.relY
		return infoDict

	

class OutputJoint(ConnectorJoint):

	def __init__(self, parent_scene, initX, initY, relX, relY):
		super(OutputJoint, self).__init__(parent_scene, initX, initY, relX, relY)
		self.tempLine = None
		self.tempConnected = None
		self.connectedInputJoint = None
		self.connectorLine = None

	def mouseMoveEvent(self, event):
		if self.tempLine == None and self.parent_scene.state == "IDLE" and self.connectedInputJoint == None:			#create a new line
			self.tempLine = self.parent_scene.addLine(self.x(), self.y(), event.scenePos().x(), event.scenePos().y())
			self.parent_scene.state = "DRAW_LINE"
			self.setBrush(red_brush)
		elif self.tempLine != None and self.parent_scene.state == "DRAW_LINE":		#update line
			self.tempLine.setLine(self.x() + 5, self.y() + 5, event.scenePos().x(), event.scenePos().y())
			self.setBrush(red_brush)
			sceneItems = self.parent_scene.items()
			mouseItems = self.parent_scene.items(event.scenePos())

			for i in sceneItems:
				if isinstance(i, InputJoint):
					i.doNonHoverCandidateActions()

			hasCandidate = False
			for i in mouseItems:
				if isinstance(i, InputJoint):
					i.doHoverCandidateActions()
					pen = QPen(Qt.red)
					pen.setWidth(5)
					self.tempLine.setPen(pen)
					hasCandidate = True
					self.tempConnected = i
					break

			if not hasCandidate:
				pen = QPen(Qt.black)
				self.tempLine.setPen(pen)
				self.tempConnected = None

	def mouseReleaseEvent(self, event):

		if self.parent_scene.state == "DRAW_LINE":
			if self.tempConnected != None:
				self.connectedInputJoint = self.tempConnected
				self.connectorLine = ConnectorLine(self.parent_scene, self, self.connectedInputJoint)
				self.connectorLine.setLine(self.pos().x() + 5, self.pos().y() + 5, self.connectedInputJoint.pos().x() + 5, self.connectedInputJoint.pos().y() + 5)
				self.connectedInputJoint.addConnectorLine(self.connectorLine)
				self.parent_scene.addItem(self.connectorLine)
				self.tempConnected.setBrush(black_brush)
				self.tempConnected.addOutputJoint(self)
				self.parent_scene.addNewConnectorLineToClipboard(self.connectorLine)

			self.parent_scene.removeItem(self.tempLine)
			self.setBrush(black_brush)
			self.tempLine = None
			self.tempConnected = None
			self.parent_scene.state = "IDLE"

	

	def adjustConnectorLine(self):
		if self.connectorLine != None:
			self.connectorLine.setLine(self.pos().x() + 5, self.pos().y() + 5, self.connectorLine.line().x2(), self.connectorLine.line().y2())


		
	def delete(self):
		injoint = self.connectedInputJoint
		inline = self.connectorLine
		if injoint != None:
			injoint.connectedOutputLines.remove(inline)
			injoint.connectedOutputJoints.remove(self)
			self.parent_scene.removeItem(self.connectorLine)
		self.parent_scene.removeItem(self)
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "output"
		if self.connectedInputJoint != None:
			infoDict["connectedNodeID"] = self.parent_scene.findNodeBelongingToConnector(self.connectedInputJoint).id
		else:
			infoDict["connectedNodeID"] = None
		return infoDict


class ConditionOutputJoint(OutputJoint):

	def __init__(self, parent_scene, initX, initY, relX, relY, cond):
		super(ConditionOutputJoint, self).__init__(parent_scene, initX, initY, relX, relY)
		self.condition = cond
		self.setAcceptHoverEvents(True)
		self.displayedCondition = QGraphicsTextItem()
		self.parent_scene.addItem(self.displayedCondition) 
	
	def hoverEnterEvent(self, event):
		self.displayedCondition.setVisible(True)
		self.displayedCondition.setPos(event.scenePos().x(), event.scenePos().y())
		self.displayedCondition.setPlainText(self.condition.displayString())
	
	def hoverLeaveEvent(self, event):
		self.displayedCondition.setVisible(False)
		self.displayedCondition.setDefaultTextColor(QColor("black"))

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "condition_output"
		infoDict["condition"] = self.condition.retrieveInfo()
		return infoDict

	def mouseMoveEvent(self, event):
		super().mouseMoveEvent(event)
		if self.parent_scene.state == "DRAW_LINE":
			col = QColor("red")
			self.displayedCondition.setDefaultTextColor(QColor("red"))
	


class InputJoint(ConnectorJoint):

	def __init__(self, parent_scene, initX, initY, relX, relY):
		super(InputJoint, self).__init__(parent_scene, initX, initY, relX, relY)
		self.setAcceptDrops(True)
		self.connectedOutputLines = []
		self.connectedOutputJoints = []
	
	def doHoverCandidateActions(self):
		brush = QBrush(Qt.red)
		self.setBrush(brush)
	
	def doNonHoverCandidateActions(self):
		brush = QBrush(Qt.black)
		self.setBrush(brush)

	def addConnectorLine(self, line):
		if line not in self.connectedOutputLines:
			self.connectedOutputLines.append(line)
	
	def addOutputJoint(self, joint):
		if joint not in self.connectedOutputJoints:
			self.connectedOutputJoints.append(joint)
	
	def delete(self):
		for line in self.connectedOutputLines:
			self.parent_scene.removeItem(line)
		for outjoint in self.connectedOutputJoints:
			outjoint.connectedInputJoint = None
		self.parent_scene.removeItem(self)
	
	def adjustConnectorLine(self):
		if len(self.connectedOutputLines) > 0:
			for connLine in self.connectedOutputLines:
				connLine.setLine(connLine.line().x1(), connLine.line().y1(), self.pos().x() + 5, self.pos().y() + 5)
	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "input"
		return infoDict
	


class ConnectorLine(QGraphicsLineItem):

	def __init__(self, parent_scene, outputJoint, inputJoint):
		super().__init__()
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setFlag(QGraphicsItem.ItemIsFocusable)
		self.setAcceptHoverEvents(True)
		pen = QPen(Qt.black)
		self.width = 2
		pen.setWidth(self.width)
		self.setPen(pen)
		self.outputJoint = outputJoint
		self.inputJoint = inputJoint
		self.parent_scene = parent_scene
	
	def keyPressEvent(self, e):
		if e.key() == Qt.Key_Delete:
			self.parent_scene.addDeleteConnectorLineToClipboard(self, self.inputJoint, self.outputJoint)
			self.remove()
	
	def remove(self):
		self.outputJoint.connectedInputJoint = None
		self.inputJoint.connectedOutputJoints.remove(self.outputJoint)
		self.inputJoint.connectedOutputLines.remove(self)
		self.parent_scene.removeItem(self)

	def updateColor(self, color):
		if color == "red":
			pen = QPen(Qt.red)
		else:
			pen = QPen(Qt.black)
		pen.setWidth(self.width)
		self.setPen(pen)