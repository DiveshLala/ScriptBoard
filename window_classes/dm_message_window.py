from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QDialogButtonBox
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
import json

class DMMessageWindow(QDialog):

	def __init__(self, labelText, messageDict):
		super().__init__()

		self.label = QLineEdit()
		self.label.setText(labelText)

		self.setWindowTitle("Send JSON message to Dialogue Manager")
		title = QLabel("Dictionary of information to send")

		self.fieldList = QTableWidget(0, 3)
		self.fieldList.setHorizontalHeaderLabels(["Field", "Type", "Value"])
		self.changedVariableNames = []

		self.jsonMessage = ""

		#buttons
		buttonLayout = QHBoxLayout()
		addButton = QPushButton("Add")
		addButton.clicked.connect(self.addToVariableList)
		removeButton = QPushButton("Remove")
		removeButton.clicked.connect(self.removeFromVariableList)
		buttonLayout.addWidget(addButton)
		buttonLayout.addWidget(removeButton)

		#titles
		titleLayout = QHBoxLayout()
		a = QLabel("Field name")
		a.setFixedWidth(200)
		b = QLabel("Type")
		b.setFixedWidth(100)
		c = QLabel("Value")
		titleLayout.addWidget(a)
		titleLayout.addWidget(b)
		titleLayout.addWidget(c)

		#variable addition
		addVariableLayout = QHBoxLayout()
		self.fieldName = QLineEdit()
		self.fieldName.setFixedWidth(200)
		addVariableLayout.addWidget(self.fieldName)

		self.typeCombo = QComboBox()
		self.typeCombo.addItem("String")
		self.typeCombo.addItem("Int")
		self.typeCombo.addItem("Float")
		self.typeCombo.addItem("Boolean")
		self.typeCombo.setFixedWidth(100)
		addVariableLayout.addWidget(self.typeCombo)

		self.defaultValue = QLineEdit()
		self.defaultValue.setFixedWidth(100)
		addVariableLayout.addWidget(self.defaultValue)
		
		self.messageDisplay = QLabel("Message ")
		self.messageDisplay.setFixedWidth(400)
		self.messageDisplay.setWordWrap(True)

		self.loadFields(messageDict)

		#OK cancel buttons
		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("Label"))
		layout.addWidget(self.label)
		layout.addWidget(title)
		layout.addWidget(self.fieldList)
		layout.addLayout(titleLayout)
		layout.addLayout(addVariableLayout)
		layout.addLayout(buttonLayout)
		layout.addWidget(self.messageDisplay)
		layout.addWidget(buttons)
		self.setLayout(layout)
	

	def loadFields(self, fields):
		rowCt = 0
		for k in fields.keys():
			self.fieldList.insertRow(rowCt)
			key_cell = QTableWidgetItem(k)
			type_cell = QTableWidgetItem(fields[k][0])
			val_cell = QTableWidgetItem(str(fields[k][1]))
			self.fieldList.setItem(rowCt, 0, key_cell)
			self.fieldList.setItem(rowCt, 1, type_cell)
			self.fieldList.setItem(rowCt, 2, val_cell)
			type_cell.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
			rowCt += 1
		self.displayMessage()

	def addToVariableList(self):
		rowCount = self.fieldList.rowCount()

		if len(self.fieldName.text().strip()) == 0:
			return
		
		for i in range(rowCount):
			if self.fieldName.text().strip() == self.fieldList.item(i, 0).text():
				return
				
		x = QTableWidgetItem(self.fieldName.text())
		y = QTableWidgetItem(self.typeCombo.currentText())          

		if len(self.defaultValue.text().strip()) == 0:
			default = ""
			if self.typeCombo.currentText() =="String":
				default = ""
			elif self.typeCombo.currentText() =="Int":
				default = 0
			elif self.typeCombo.currentText() =="Float":
				default = 0.0
			elif self.typeCombo.currentText() =="Boolean":
				default = False
			z = QTableWidgetItem(str(default))
		else:
			default = self.defaultValue.text().strip()
			if self.typeCombo.currentText() =="Int":
				try:
					int(default)
				except ValueError as e:
					print("Default value must be an int")
					return
			elif self.typeCombo.currentText() =="Float":
				try:
					float(default)
				except ValueError as e:
					print("Default value must be a float")
					return
			elif self.typeCombo.currentText() == "Boolean":
				legalVals = ["true", "false"]
				if default.lower() not in legalVals:
					return
				
			z = QTableWidgetItem(default)

		x.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
		y.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
		z.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
		self.fieldList.insertRow(rowCount)
		self.fieldList.setItem(rowCount, 0, x) 
		self.fieldList.setItem(rowCount, 1, y) 
		self.fieldList.setItem(rowCount, 2, z)
		self.displayMessage()

	
	def displayMessage(self):
		rowCount = self.fieldList.rowCount()
		if rowCount == 0:
			self.jsonMessage = ""
			self.messageDisplay.setText("Message ")
			return
		
		try:
			jsonDict = {}
			for i in range(rowCount):
				type_val = self.fieldList.item(i, 1).text()
				val = self.fieldList.item(i, 2).text()
				if type_val == "Int":
					val = int(val)
				elif type_val == "Float":
					val = float(val)
				elif type_val == "Boolean":
					val = bool(val)
				jsonDict[self.fieldList.item(i, 0).text()] = val
			self.jsonMessage = json.dumps(jsonDict)
			self.messageDisplay.setText("Message " + self.jsonMessage)
			self.messageDict = jsonDict
		except TypeError as e:
			print("Could not make JSON!")
			print(e)


	def removeFromVariableList(self):
		curRow = self.fieldList.currentRow()
		if self.fieldList.item(curRow, 0) == None:
			return
		self.fieldList.removeRow(curRow)
		self.displayMessage()

	
	def getVariableList(self):
		data = []
		for x in range(self.fieldList.rowCount()):
			variableInfo = []
			for y in range(self.fieldList.columnCount()):
				variableInfo.append(self.fieldList.item(x, y).text())
			data.append(variableInfo)
		return data
	
	def get_message_dict(self):
		message_dict = {}
		rowCount = self.fieldList.rowCount()
		for i in range(rowCount):
			k = self.fieldList.item(i, 0).text()
			val_type = self.fieldList.item(i, 1).text()
			val = self.fieldList.item(i, 2).text()
			if val_type == "Int":
				val = int(val)
			elif val_type == "Float":
				val = float(val)
			elif val_type == "Boolean":
				val = bool(val)
			message_dict[k] = [val_type, val]
		return message_dict
