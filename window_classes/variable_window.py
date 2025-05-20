from PyQt5.QtWidgets import QMessageBox,  QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem
from PyQt5 import QtCore

class VariableWindow(QDialog):

	def __init__(self, mainWindow):
		super().__init__()

		self.setWindowTitle("Variable Setting")
		self.parentWindow = mainWindow
		self.parentScene = self.parentWindow.scene

		title = QLabel("Variables to track during interaction")

		self.variableList = QTableWidget(0, 3)
		self.variableList.setHorizontalHeaderLabels(["Variable name", "Type", "Initial value"])
		self.variableList.currentItemChanged.connect(self.storeValue)
		self.variableList.itemChanged.connect(self.confirmValue)
		self.previousValue = None
		self.changedVariableNames = []

		self.loadVariables(mainWindow.variables)
		
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
		a = QLabel("Variable name")
		a.setFixedWidth(200)
		b = QLabel("Type")
		b.setFixedWidth(100)
		c = QLabel("Initial value")
		titleLayout.addWidget(a)
		titleLayout.addWidget(b)
		titleLayout.addWidget(c)

		#variable addition
		addVariableLayout = QHBoxLayout()
		self.varName = QLineEdit()
		self.varName.setFixedWidth(200)
		addVariableLayout.addWidget(self.varName)

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

		#OK cancel buttons
		closeLayout = QHBoxLayout()
		closeButton = QPushButton("Close")
		closeButton.setFixedWidth(100)
		closeButton.clicked.connect(lambda:self.close())
		closeLayout.addStretch(1)
		closeLayout.addWidget(closeButton)
		closeLayout.addStretch(1)


		layout = QVBoxLayout()
		layout.addWidget(title)
		layout.addWidget(self.variableList)
		layout.addLayout(titleLayout)
		layout.addLayout(addVariableLayout)
		layout.addLayout(buttonLayout)
		layout.addLayout(closeLayout)
		self.setLayout(layout)
	

	def loadVariables(self, variables):
		rowCt = 0
		for v in variables:
			self.variableList.insertRow(rowCt)
			for i, item in enumerate(v):
				cell = QTableWidgetItem(item)
				self.variableList.setItem(rowCt, i, cell)
				if i == 1:
					cell.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
			rowCt += 1

	def addToVariableList(self):
		rowCount = self.variableList.rowCount()

		if len(self.varName.text().strip()) == 0:
			return
		
		for i in range(rowCount):
			if self.varName.text().strip() == self.variableList.item(i, 0).text():
				return
		
		if not self.varName.text().isidentifier():
			print("Must be a valid variable name")
			return
		
		x = QTableWidgetItem(self.varName.text())
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

		y.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
		self.variableList.insertRow(rowCount)
		self.variableList.setItem(rowCount, 0, x) 
		self.variableList.setItem(rowCount, 1, y) 
		self.variableList.setItem(rowCount, 2, z)
		self.parentWindow.variables.append([self.varName.text(), self.typeCombo.currentText(), self.defaultValue.text()])
		self.parentScene.setSceneChanged(True)


	def removeFromVariableList(self):
		curRow = self.variableList.currentRow()
		if self.variableList.item(curRow, 0) == None:
			return
		varName = self.variableList.item(curRow, 0).text()
		if self.parentScene.doesNodeUseVariable(varName):
			dlg = QMessageBox()
			dlg.setWindowTitle("Delete variable?")
			dlg.setText("This variable will be removed from the script. Are you sure you want to delete it?")
			dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			ret = dlg.exec()
			if ret == QMessageBox.Yes:
				self.parentScene.removeVariableFromScript(varName)
				self.variableList.removeRow(curRow)
				self.parentScene.setSceneChanged(True)
		else:
			self.variableList.removeRow(curRow)
			self.parentScene.setSceneChanged(True)

	
	def getVariableList(self):
		data = []
		for x in range(self.variableList.rowCount()):
			variableInfo = []
			for y in range(self.variableList.columnCount()):
				variableInfo.append(self.variableList.item(x, y).text())
			data.append(variableInfo)
		return data

	def storeValue(self, item):
		if item == None:
			return
		self.previousValue = self.variableList.item(item.row(), item.column()).text()

	def confirmValue(self, item):

		if self.previousValue == None:
			return
	
		#nothing actually selected, so ignore
		if len([x.row() for x in self.variableList.selectedIndexes()]) == 0:
			return

		oldVal = self.previousValue
		newVal = self.variableList.item(item.row(), item.column()).text()

		if oldVal == newVal:
			return

		#check for change of variable name
		if item.column() == 0:
			curVars = [self.variableList.item(i, 0).text().strip() for i in range(self.variableList.rowCount()) if i != item.row()]
			if not newVal.isidentifier():
				msgBox = QMessageBox()
				msgBox.setText("Please choose a valid variable name (alphanumeric, cannot start with a number)")
				msgBox.exec()
				cell = QTableWidgetItem(oldVal)
				self.variableList.setItem(item.row(), item.column(), cell)
				self.previousValue = oldVal
			elif newVal.strip() in curVars:
				msgBox = QMessageBox()
				msgBox.setText("Variable name already exists!")
				msgBox.exec()
				cell = QTableWidgetItem(oldVal)
				self.variableList.setItem(item.row(), item.column(), cell)
				self.previousValue = oldVal
			else:
				if self.parentScene.doesNodeUseVariable(oldVal):
					self.parentWindow.updateVariableName(oldVal, newVal)
					msgBox = QMessageBox()
					msgBox.setText("Following variable name has changed:\n" + oldVal + " -> " + newVal)
					msgBox.exec()
				self.previousValue = newVal
				self.parentScene.setSceneChanged(True)

		#check for change of variable value
		elif item.column() == 2:
			varType = self.variableList.item(item.row(), 1).text()
			valid = True
			if varType == "Int":
				try:
					int(newVal)
				except ValueError:
					valid = False
					msgBox = QMessageBox()
					msgBox.setText("Int value must be a whole number!")
					msgBox.exec()
			elif varType == "Float":
				try:
					float(newVal)
				except ValueError:
					valid = False
					msgBox = QMessageBox()
					msgBox.setText("Float value must be a number!")
					msgBox.exec()
			elif varType == "Boolean":
				validBools = ["true", "false"]
				if newVal.lower().strip() not in validBools:
					valid = False
					msgBox = QMessageBox()
					msgBox.setText("Boolean value must be 'true' or 'false'")
					msgBox.exec()

			if not valid:
				cell = QTableWidgetItem(oldVal)
				self.variableList.setItem(item.row(), item.column(), cell)
				self.previousValue = oldVal
			else:
				self.parentScene.setSceneChanged(True)