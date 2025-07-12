from PyQt5.QtWidgets import QTextEdit, QSpinBox, QListView, QDialogButtonBox, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QPushButton, QAbstractItemView, QComboBox, QFrame
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QTextCursor, QTextCharFormat, QFont

class VariableUpdateWindow(QDialog):
	def __init__(self, initUpdate, variableList, environment):
		super().__init__()
		self.updates = []
		self.originalVariables = variableList

		self.setWindowTitle("Update variables")
		listLayout = QHBoxLayout()
		self.updateList = QListView()
		self.itemModel = QStandardItemModel()
		self.updateList.setModel(self.itemModel)
		self.updateList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.removeButton = QPushButton("Remove")
		self.removeButton.clicked.connect(self.removeUpdate)
		for x in initUpdate:
			self.updates.append(x)
			c = QStandardItem(x[0] + "=" + str(x[1]))
			self.itemModel.appendRow(c)
		self.removeButton.setEnabled(self.itemModel.rowCount() > 0)
		listLayout.addWidget(self.updateList)
		listLayout.addWidget(self.removeButton)

		variableSelectLayout = QHBoxLayout()


		#directly update variable
		directUpdateLayout = QHBoxLayout()
		directUpdateLayout.setSpacing(30)
		variableNames = [x[0] for x in variableList]
		usedVariableNames = [x[0] for x in self.updates]
		availableVariables = [x for x in variableList if x[0] not in usedVariableNames]
		self.variableNameCombo = QComboBox()
		[self.variableNameCombo.addItem(x) for x in variableNames if x not in usedVariableNames]
		self.variableNameCombo.currentIndexChanged.connect(self.comboChanged)

		self.variableType = QLabel(variableList[0][1])
		self.variableType.setFixedWidth(50)
		self.variableType.setAlignment(QtCore.Qt.AlignCenter)
		if len(availableVariables) > 0:
			self.variableType.setText(availableVariables[0][1])

		self.variableUpdateValue = QLineEdit()
		self.setValueButton = QPushButton("Set Direct Value")
		self.setValueButton.clicked.connect(self.addVariableUpdate)

		if self.variableNameCombo.count() == 0:
			self.setValueButton.setEnabled(False)

		#variable calculation
		calculationLayout = QHBoxLayout()
		calculationLayout.setContentsMargins(0,0,0,0)
		self.calculationCombo = QComboBox()
		[self.calculationCombo.addItem("Variable(" + x[0] + ")") for x in variableList if (x[1] == "Int" or x[1] == "Float")] 
		self.mathExpression = QComboBox()
		self.mathExpression.addItems(["+", "-", "*", "/"])
		self.calculatedValue = QLineEdit()
		self.calculatedValue.setFixedWidth(50)
		self.calculatedValueButton = QPushButton("Set Calculated Value")
		self.calculatedValueButton.clicked.connect(self.addVariableUpdateCalculated)
		self.calculationFrame = QFrame()
		self.calculationFrame.setLayout(calculationLayout)

		#string append
		stringAppendLayout = QHBoxLayout()
		stringAppendLayout.setContentsMargins(0,0,0,0)
		self.stringCombo = QComboBox()
		self.stringCombo.setFixedWidth(300)
		[self.stringCombo.addItem("Variable(" + x[0] + ")") for x in variableList if (x[1] == "String")]
		self.stringCombo.addItems(["Target's utterance", "Target's turn"])
		humans = [x[0] for x in environment]
		[self.stringCombo.addItem("Human " + str(human) + " utterance") for human in humans]
		[self.stringCombo.addItem("Human " + str(human) + " turn") for human in humans]
		self.stringAppendButton = QPushButton("Set Appended Value")
		self.stringAppendButton.clicked.connect(self.addVariableUpdateStringAppend)
		self.appendFrame = QFrame()
		self.appendFrame.setLayout(stringAppendLayout)

		self.setLayoutVisibility()

	
		#ok cancel buttons
		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		variableSelectLayout.addWidget(self.variableNameCombo)
		variableSelectLayout.addWidget(self.variableType)

		directUpdateLayout.addWidget(self.variableUpdateValue)
		directUpdateLayout.addWidget(self.setValueButton)
		
		calculationLayout.addWidget(self.calculationCombo)
		calculationLayout.addWidget(self.mathExpression)
		calculationLayout.addWidget(self.calculatedValue)
		calculationLayout.addStretch(1)
		calculationLayout.addWidget(self.calculatedValueButton)

		stringAppendLayout.addWidget(self.stringCombo)
		stringAppendLayout.addWidget(self.stringAppendButton)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("Variable"))
		layout.addLayout(variableSelectLayout)
		layout.addLayout(listLayout)
		layout.addWidget(QLabel("Enter direct value"))
		layout.addLayout(directUpdateLayout)
		layout.addWidget(QLabel("Calculate value"))
		layout.addWidget(self.calculationFrame)
		layout.addWidget(self.appendFrame)
		layout.addWidget(confirmButtons)
		self.setLayout(layout)
	
	def setLayoutVisibility(self):
		calcShow = self.variableType.text() in ["Int", "Float"] 
		appendShow = self.variableType.text() == "String"
		if calcShow:
			self.calculationFrame.show()
			self.appendFrame.hide()
		elif appendShow:
			self.calculationFrame.hide()
			self.appendFrame.show()
		else:
			self.calculationFrame.hide()
			self.appendFrame.hide()
	
	def addVariableUpdate(self):
		if self.variableNameCombo.currentText() == "":
			return 
		value = self.variableUpdateValue.text()
		variableType = self.variableType.text()

		if variableType == "Int":
			try:
				int(value)
			except ValueError as e:
				msgBox = QMessageBox()
				msgBox.setText("Int value must be a whole number!")
				msgBox.exec()
				return
		elif variableType == "Float":
			try:
				float(value)
			except ValueError as e:
				msgBox = QMessageBox()
				msgBox.setText("Float value must be a number!")
				msgBox.exec()
				return
		elif variableType == "Boolean":
			validVals = ["true", "false"]
			if value.lower().strip() not in validVals:
				msgBox = QMessageBox()
				msgBox.setText("Boolean value must be \"true\" or \"false\"!")
				msgBox.exec()
				return 
		self.updates.append([self.variableNameCombo.currentText(), value])
		self.updateGUI()


	def addVariableUpdateCalculated(self):
		if self.variableNameCombo.currentText() == "":
			return 
		
		value = self.calculatedValue.text()
		variableType = self.variableType.text()

		if variableType == "Int":
			try:
				int(value)
			except ValueError as e:
				msgBox = QMessageBox()
				msgBox.setText("Int value must be a whole number!")
				msgBox.exec()
				return
		elif variableType == "Float":
			try:
				float(value)
			except ValueError as e:
				msgBox = QMessageBox()
				msgBox.setText("Float value must be a number!")
				msgBox.exec()
				return
			
		self.updates.append([self.variableNameCombo.currentText(), self.calculationCombo.currentText() + self.mathExpression.currentText() + value])
		self.updateGUI()

	
	def updateGUI(self):
		self.variableUpdateValue.clear()
		self.variableNameCombo.removeItem(self.variableNameCombo.currentIndex())
		self.refreshUpdateList()
		self.updateList.selectionModel().select(self.itemModel.index(0, 0), QtCore.QItemSelectionModel.Select)

	
	def addVariableUpdateStringAppend(self):
		if self.variableNameCombo.currentText() == "":
			return 
	
		value = self.stringCombo.currentText()
		
		self.updates.append([self.variableNameCombo.currentText(), "Variable(" + self.variableNameCombo.currentText() + ")" + "+" + value])
		self.updateGUI()
	
	def removeUpdate(self):
		try:
			selectedIndex = self.updateList.selectedIndexes()[0].row()
		except IndexError:
			return
		removedVariable = self.updates[selectedIndex][0]
		self.updates = [x for ind, x in enumerate(self.updates) if ind != selectedIndex]
		self.refreshUpdateList()
		self.variableNameCombo.addItem(removedVariable)
		self.setValueButton.setEnabled(True)
		if self.itemModel.rowCount() == 0:
			self.removeButton.setEnabled(False)
	
	def comboChanged(self):
		v = self.variableNameCombo.currentText()
		if self.variableNameCombo.currentIndex() == -1:
			self.variableType.setText("")
			self.setValueButton.setEnabled(False)
			return
		varType = [x[1] for x in self.originalVariables if x[0] == v][0]
		self.variableType.setText(varType)
		self.setLayoutVisibility()

	def refreshUpdateList(self):
		self.itemModel.clear()
		for x in self.updates:
			c = QStandardItem(x[0] + "=" + x[1])
			self.itemModel.appendRow(c)
		if self.updateList.model().rowCount() > 0:
			self.updateList.selectionModel().select(self.itemModel.index(0, 0), QtCore.QItemSelectionModel.Select)
			self.removeButton.setEnabled(True)
		else:
			self.removeButton.setEnabled(False)


class LLMVariableUpdateWindow(QDialog):
	def __init__(self, initLabel, initPrompt, initVariable, variableList):
		super().__init__()

		self.variableList = variableList

		self.setWindowTitle("LLM Variable update")
		layout = QVBoxLayout()

		if initPrompt != None:
			initPromptText = initPrompt.text_prompt
			initSpeakers = initPrompt.speakers
			initHistory = initPrompt.history
			initTurns = initPrompt.numTurns
		else:
			initPromptText = ""
			initSpeakers = ""
			initHistory = ""
			initTurns = 0

		self.label = QLineEdit()
		self.label.setFixedWidth(300)
		self.label.setText(initLabel)

		promptLayout = QHBoxLayout()
		self.promptBox = QTextEdit()
		self.promptBox.setFixedHeight(500)
		self.promptBox.setFixedWidth(800)
		self.setInitialPrompt(initPromptText)

		insertLayout = QVBoxLayout()
		self.inputVariableCombo = QComboBox()
		self.inputVariableCombo.addItems([x[0] for x in variableList])
		self.insertButton = QPushButton("Insert variable")
		self.insertButton.clicked.connect(self.insertVariableString)
		insertLayout.addStretch(1)
		insertLayout.addWidget(self.inputVariableCombo)
		insertLayout.addWidget(self.insertButton)
		insertLayout.addStretch(1)
		promptLayout.addWidget(self.promptBox)
		promptLayout.addLayout(insertLayout)

		self.participantCombo = QComboBox()
		self.participantCombo.setFixedWidth(300)
		self.participantCombo.addItems(["None", "All", "Users only", "Target user only", "Non-target user only", "Robot only"])
		self.participantCombo.currentIndexChanged.connect(self.changeParticipantCombo)

		self.contextCombo = QComboBox()
		self.contextCombo.setFixedWidth(300)
		self.contextCombo.addItems(["Whole dialog history", "Most recent turns"])
		self.contextCombo.currentIndexChanged.connect(self.changeContextCombo)

		self.numTurns = QSpinBox()
		self.numTurns.setFixedWidth(50)
		self.numTurns.setMinimum(1)
		self.numTurns.setMaximum(100)
		self.numTurns.setSingleStep(1)

		variableLayout = QHBoxLayout()
		self.variableCombo = QComboBox()
		self.variableCombo.setFixedWidth(200)
		self.variableCombo.addItems([x[0] for x in variableList])
		self.variableCombo.currentIndexChanged.connect(self.changeVariableCombo)
		self.variableType = QLabel("")

		variableLayout.addWidget(self.variableCombo)
		variableLayout.addWidget(self.variableType)

		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Label"))
		layout.addWidget(self.label)
		layout.addWidget(QLabel("Prompt"))
		layout.addLayout(promptLayout)
		layout.addWidget(QLabel("Information to be added below prompt"))
		layout.addWidget(QLabel("Whose utterances to add?"))
		layout.addWidget(self.participantCombo)
		layout.addWidget(QLabel("Which dialog to add?"))
		layout.addWidget(self.contextCombo)
		layout.addWidget(QLabel("Maximum number of turns to be added"))
		layout.addWidget(self.numTurns)
		layout.addWidget(QLabel("Which variable to store result?"))
		layout.addLayout(variableLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)

		if len(initSpeakers) > 0:
			self.participantCombo.setCurrentText(initSpeakers) 
		
		if len(initHistory) > 0:
			self.contextCombo.setCurrentText(initHistory)
		
		if initTurns > 0:
			self.numTurns.setValue(initTurns)
		
		if initVariable != None:
			self.variableCombo.setCurrentText(initVariable)
		
		self.changeContextCombo()
		self.changeParticipantCombo()
		self.changeVariableCombo()
	
	def changeParticipantCombo(self):
		self.contextCombo.setEnabled(self.participantCombo.currentText() != "None")
		if self.participantCombo.currentText() == "None":
			self.numTurns.setEnabled(False)
		else:
			self.changeContextCombo()

	def changeContextCombo(self):
		self.numTurns.setEnabled(self.contextCombo.currentText() != "Whole dialog history")
	
	def changeVariableCombo(self):
		for v in self.variableList:
			if v[0] == self.variableCombo.currentText():
				self.variableType.setText(v[1])
	
	def insertVariableString(self):
		cursor = self.getCursor("Bold")
		self.insertText(cursor, "Variable(" + str(self.inputVariableCombo.currentText()) + ")")
		#change back to regular cursor
		cursor = self.getCursor()
	
	def getCursor(self, type="Normal"):
		cursor = QTextCursor(self.promptBox.textCursor())
		format = QTextCharFormat(cursor.charFormat())
		if type == "Bold":
			format.setFontWeight(QFont.Bold)
		else:
			format.setFontWeight(QFont.Normal)
		cursor.setCharFormat(format)
		self.promptBox.setTextCursor(cursor)
		return cursor
	
	def insertText(self, cursor, text):
		self.promptBox.moveCursor(QTextCursor.End)
		cursor.insertText(text)
		self.promptBox.moveCursor(QTextCursor.End)
	
	def setInitialPrompt(self, text):

		if len(text) == 0:
			return

		varStartIndices = [i for i in range(len(text)) if text.startswith("Variable(", i)]

		if len(varStartIndices) == 0:
			self.promptBox.setText(text)
		else:
			nonVarStart = 0

			for i in varStartIndices:
				#set normal font
				cursor = self.getCursor()
				self.insertText(cursor, text[nonVarStart:i])

				#set bold font
				cursor = self.getCursor("Bold")
				endIndex = text.find(")", i) + 1
				varText = text[i:endIndex]
				self.insertText(cursor, varText)

				nonVarStart = endIndex
	
			cursor = self.getCursor()
			self.insertText(cursor, text[endIndex:len(text)])

		# #change to normal font
		cursor = self.getCursor()