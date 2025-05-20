from PyQt5.QtWidgets import QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QPushButton, QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt

class EnvironmentWindow(QDialog):
	def __init__(self, initHumanData, parentWindow):
		super().__init__()
		self.setWindowTitle("Human designation")
		title = QLabel("Set up the interaction")
		self.parentScene = parentWindow.scene

		self.humanList = QTableWidget(0, 2)
		self.humanList.setHorizontalHeaderLabels(["Human ID", "Set as target"])
		self.humanList.horizontalHeader().resizeSection(0, 100)

		self.loadVariables(initHumanData)

		#add human 
		addHumanLayout = QHBoxLayout()
		self.numHumanSpin = QSpinBox()
		self.numHumanSpin.setMinimum(0)
		addHumanLayout.addWidget(QLabel("Add human with ID"))
		addHumanLayout.addWidget(self.numHumanSpin)

		#buttons
		buttonLayout = QHBoxLayout()
		addButton = QPushButton("Add human")
		addButton.clicked.connect(self.addHuman)
		removeButton = QPushButton("Remove human")
		removeButton.clicked.connect(self.removeHuman)
		buttonLayout.addWidget(addButton)
		buttonLayout.addWidget(removeButton)

		#ok cancel buttons
		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		layout = QVBoxLayout()
		layout.addWidget(title)
		layout.addWidget(self.humanList)
		layout.addLayout(addHumanLayout)
		layout.addLayout(buttonLayout)
		layout.addWidget(confirmButtons)
		self.setLayout(layout)
	
	def addHuman(self):
		rowCount = self.humanList.rowCount()
		idNum = self.numHumanSpin.value()
		#check if id is unique
		for i in range(rowCount):
			if str(idNum) == self.humanList.item(i, 0).text():
				return
		
		targetCheck = QCheckBox()
		targetCheck.stateChanged.connect(lambda: self.updateChecks())
		self.humanList.insertRow(rowCount)
		self.humanList.setItem(rowCount, 0, QTableWidgetItem(str(idNum)))
		self.humanList.setCellWidget(rowCount, 1, targetCheck)

		if self.humanList.rowCount() == 1:
			cbox = self.humanList.cellWidget(0, 1)
			cbox.setCheckState(True)
		self.parentScene.setSceneChanged(True)

	
	def removeHuman(self):
		curRow = self.humanList.currentRow()
		self.humanList.removeRow(curRow)
		self.parentScene.setSceneChanged(True)
		self.updateChecks()

	#ensure that only one targetcan be checked	
	def updateChecks(self):
		rowCount = self.humanList.rowCount()
		checkedBox = None
		for i in range(rowCount):
			c = self.humanList.cellWidget(i, 1)
			if c.isChecked():
				checkedBox = c				
				break
		for i in range(rowCount):
			c = self.humanList.cellWidget(i, 1)
			if checkedBox != None and c != checkedBox:
				c.setEnabled(False)
			else:
				c.setEnabled(True)
		self.parentScene.setSceneChanged(True)
	
	def getHumanData(self):
		humans = []
		rowCount = self.humanList.rowCount()
		for i in range(rowCount):
			hid = self.humanList.item(i, 0).text()
			c = self.humanList.cellWidget(i, 1)
			humans.append([int(hid), c.isChecked()])
		return humans

	def loadVariables(self, humanData):
		rowCt = 0
		for x in humanData:
			self.humanList.insertRow(rowCt)
			self.humanList.setItem(rowCt, 0, QTableWidgetItem(str(x[0])))
			targetCheck = QCheckBox()
			targetCheck.setTristate(False)
			self.humanList.setCellWidget(rowCt, 1, targetCheck)
			targetCheck.setCheckState(x[1])
			targetCheck.stateChanged.connect(lambda: self.updateChecks())
			rowCt += 1