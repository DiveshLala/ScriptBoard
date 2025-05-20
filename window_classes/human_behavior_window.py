from PyQt5.QtWidgets import QGroupBox, QWidget, QListView, QDialogButtonBox, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QPushButton, QAbstractItemView, QSpinBox, QComboBox, QCheckBox
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from condition import Condition, MultiCondition
from condition import isConditionValid
import os

class HumanBehaviorWindow(QDialog):
	def __init__(self, initConditions, variables, environment):
		super().__init__()

		self.setWindowTitle("Human Speech")
		self.conditions = []
		self.variables = variables
		self.conditionList = QListView()

		self.conditionList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.conditionList.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.silenceCondition = None
		self.timerCondition = None
		self.itemModel = QStandardItemModel()
		self.conditionList.setModel(self.itemModel)

		conditionListLayout = QHBoxLayout()
		listModLayout = QVBoxLayout()

		self.moveUpButton = QPushButton("Up")
		self.moveUpButton.clicked.connect(self.moveConditionUp)
		self.moveDownButton = QPushButton("Down")
		self.moveDownButton.clicked.connect(self.moveConditionDown)
		self.combineButton = QPushButton("Combine AND")
		self.combineButton.clicked.connect(self.mergeConditions)
		self.editValueButton = QPushButton("Edit Value")
		self.editValueButton.clicked.connect(self.editValue)

		self.removeConditionButton = QPushButton("Remove")
		self.removeConditionButton.clicked.connect(self.removeCondition)

		self.disableButtons()

		listModLayout.addWidget(self.moveUpButton)
		listModLayout.addWidget(self.moveDownButton)
		listModLayout.addWidget(self.combineButton)
		listModLayout.addWidget(QWidget())
		listModLayout.addWidget(self.editValueButton)
		listModLayout.addWidget(self.removeConditionButton)
		conditionListLayout.addWidget(self.conditionList)
		conditionListLayout.addLayout(listModLayout)

		human_ids = [x[0] for x in environment]

		self.speechObjects =["Human " + str(hid) +  " utterance" for hid in human_ids] + ["Target's turn", "Target's utterance", "Non-target's turn", "Non-target's utterance", "Anyone's utterance", "Anyone's turn"]
		self.speechStringComparators = ["is anything", "equals", "contains", "contains word", "starts with", "ends with", "does not equal", "does not contain", "does not start with", "does not end with", "word length greater than", "word length less than", "character length greater than", "character length less than"]


		#condition for speech
		speechConditionLayout = QHBoxLayout()
		self.speechObjectCombo = QComboBox()
		[self.speechObjectCombo.addItem(x) for x in self.speechObjects]
		self.speechComparatorCombo = QComboBox()
		self.speechComparatorCombo.setFixedWidth(300)
		[self.speechComparatorCombo.addItem(x) for x in self.speechStringComparators]
		self.speechComparatorCombo.currentIndexChanged.connect(self.speechComparatorChanged)

		speechValueLayout = QVBoxLayout()
		speechValueLayout.setAlignment(Qt.AlignTop)
		self.speechValueEntry = QLineEdit()
		self.speechValueEntry.setFixedWidth(500)
		self.speechValueEntry.setEnabled(False)
		speechValueLayout.addWidget(self.speechValueEntry)
		
		addSpeechConditionButton = QPushButton("Add")
		addSpeechConditionButton.clicked.connect(self.addSpeechCondition)

		styleString = "QGroupBox { border: 1px solid black; padding-top: 10px;}"


		textConditionGroup = QGroupBox("Speech condition (text)")
		textConditionGroup.setStyleSheet(styleString)
		container = QVBoxLayout()
		container.addWidget(QLabel("Create a text condition for speech received. Use semi-colon (;) to specify multiple OR conditions"))
		container.addLayout(speechConditionLayout)
		speechConditionLayout.setAlignment(Qt.AlignRight)
		speechConditionLayout.addWidget(self.speechObjectCombo)
		speechConditionLayout.addWidget(self.speechComparatorCombo)
		speechConditionLayout.addLayout(speechValueLayout)
		speechConditionLayout.addWidget(addSpeechConditionButton)
		textConditionGroup.setLayout(container)

		#condition for word lists
		listConditionLayout = QHBoxLayout()
		self.listObjectCombo = QComboBox()
		[self.listObjectCombo.addItem(x) for x in self.speechObjects]
		self.listComparatorCombo = QComboBox()
		self.listStringComparators = ["equals", "contains", "contains word", "starts with", "ends with", "does not equal", "does not contain", "does not start with", "does not end with"]
		[self.listComparatorCombo.addItem(x) for x in self.listStringComparators]

		listValueLayout = QVBoxLayout()
		self.listValueEntry = QComboBox()
		for x in os.listdir("./word_lists/"):
			if x.endswith(".words"):
				self.listValueEntry.addItem(x.replace(".words", ""))
		self.listValueEntry.setFixedWidth(200)
		listValueLayout.addWidget(self.listValueEntry)
		
		addListConditionButton = QPushButton("Add")
		addListConditionButton.clicked.connect(self.addListCondition)
		addListConditionButton.setFixedWidth(100)

		listConditionGroup = QGroupBox("Speech condition (word list)")
		listConditionGroup.setStyleSheet(styleString)
		container = QVBoxLayout()
		container.addWidget(QLabel("Create a word list condition for speech received"))
		container.addLayout(listConditionLayout)

		# listConditionLayout.setAlignment(Qt.AlignRight)
		listConditionLayout.addWidget(self.listObjectCombo)
		listConditionLayout.addWidget(self.listComparatorCombo)
		listConditionLayout.addLayout(listValueLayout)
		listConditionLayout.addWidget(addListConditionButton)
		listConditionGroup.setLayout(container)

		#condition for variables
		self.stringComparators = ["is anything", "equals", "contains", "contains word", "starts with", "ends with", "does not equal", "does not contain", "does not start with", "does not end with", "word length greater than", "word length less than", "character length greater than", "character length less than"]
		self.numericComparators = ["=", ">", "<", ">=", "<="]
		self.boolComparators = ["true", "false"]

		variableConditionLayout = QHBoxLayout()
		self.variableCombo = QComboBox()
		self.variableCombo.setFixedWidth(200)
		[self.variableCombo.addItem(x[0]) for x in variables]
		self.variableCombo.currentIndexChanged.connect(self.variableChanged)
		
		self.variableType = QLabel()
		if len(variables) > 0:
			self.variableType.setText(variables[0][1])
		self.variableType.setFixedWidth(75)
		self.variableType.setAlignment(QtCore.Qt.AlignCenter)

		self.variableComparatorCombo = QComboBox()
		if self.variableType.text() == "String":
			[self.variableComparatorCombo.addItem(x) for x in self.stringComparators]
		elif self.variableType.text() == "Int" or self.variableType.text() == "Float":
			[self.variableComparatorCombo.addItem(x) for x in self.numericComparators]
		elif self.variableType.text() == "Boolean":
			[self.variableComparatorCombo.addItem(x) for x in self.boolComparators]
		self.variableComparatorCombo.currentIndexChanged.connect(self.variableComparatorChanged)
		self.variableComparatorCombo.setFixedWidth(300)
		
		self.variableValue = QLineEdit()
		self.variableValue.setFixedWidth(300)
		if self.variableType.text() == "String":
			self.variableValue.setEnabled(False)

		addVariableConditionButton = QPushButton("Add")
		addVariableConditionButton.clicked.connect(self.addVariableCondition)

		variableConditionGroup = QGroupBox("Speech condition (variable)")
		variableConditionGroup.setStyleSheet(styleString)
		container = QVBoxLayout()
		container.addWidget(QLabel("Create a variable condition for speech received"))
		container.addLayout(variableConditionLayout)

		variableConditionLayout.addWidget(self.variableCombo)
		variableConditionLayout.addWidget(self.variableType)
		variableConditionLayout.addWidget(self.variableComparatorCombo)
		variableConditionLayout.addWidget(self.variableValue)
		variableConditionLayout.addStretch(1)
		variableConditionLayout.addWidget(addVariableConditionButton)
		variableConditionGroup.setLayout(container)


		#condition for silence
		silenceConditionLayout = QHBoxLayout()
		silenceConditionLayout.setSpacing(20)
		self.silenceCheck = QCheckBox()
		self.silenceCheck.setChecked(self.silenceCondition != None)
		self.silenceValue = QSpinBox()
		self.silenceValue.setMinimum(500)
		self.silenceValue.setMaximum(100000)
		self.silenceValue.setSingleStep(500)
		self.silenceValue.lineEdit().setReadOnly(True)
		self.silenceValue.valueChanged.connect(self.updateSilenceCondition)
		self.silenceCheck.stateChanged.connect(self.updateSilenceCondition)
		self.silenceLabel = QLabel("Silence time (ms) greater than")

		silenceConditionLayout.addWidget(QLabel("Make a condition for user silence?"))
		silenceConditionLayout.addWidget(self.silenceCheck)
		silenceConditionLayout.addWidget(self.silenceLabel)
		silenceConditionLayout.addWidget(self.silenceValue)
		silenceConditionLayout.addStretch(1)

		#condition for timer
		timerConditionLayout = QHBoxLayout()
		timerConditionLayout.setSpacing(20)
		self.timerCheck = QCheckBox()
		self.timerCheck.setChecked(self.timerCondition != None)
		self.timerCheck.stateChanged.connect(self.updateTimerCondition)

		timerConditionLayout.addWidget(QLabel("Make a condition for the timer elapsing?"))
		timerConditionLayout.addWidget(self.timerCheck)
		timerConditionLayout.addStretch(1)

		#confirm buttons
		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("Conditions (order of priority)"))
		layout.addLayout(conditionListLayout)
		layout.addWidget(textConditionGroup)
		layout.addWidget(listConditionGroup)
		layout.addWidget(variableConditionGroup)
		layout.addLayout(silenceConditionLayout)
		layout.addLayout(timerConditionLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)

		self.conditionList.selectionModel().selectionChanged.connect(self.listSelectionChanged)

		for cond in initConditions:
			if isinstance(cond, Condition) and cond.targetObject == "Silence time":
				self.silenceCondition = cond
			elif isinstance(cond, Condition) and cond.targetObject == "Timer":
				self.timerCondition = cond
			else:
				self.conditions.append(cond)
		self.refreshConditions()
	
	def updateSilenceCondition(self):
		self.silenceLabel.setEnabled(self.silenceCheck.isChecked())
		self.silenceValue.setEnabled(self.silenceCheck.isChecked())
		if self.silenceCheck.isChecked():
			c = Condition()
			c.updateCondition("Silence time", "greater than", self.silenceValue.value(), "Int")
			self.silenceCondition = c
		else:
			self.silenceCondition = None
	
	def updateTimerCondition(self):
		if self.timerCheck.isChecked():
			c = Condition()
			c.updateCondition("Timer", "time elapsed", True, "Boolean")
			self.timerCondition = c
		else:
			self.timerCondition = None
		
	def variableChanged(self):
		comboVal = self.variableCombo.currentText()
		currentVar = None
		for x in self.variables:
			if x[0] == comboVal:
				currentVar = x
				break

		varType = currentVar[1]
		self.variableType.setText(varType)
		self.variableComparatorCombo.clear()
		if varType == "String":
			[self.variableComparatorCombo.addItem(x) for x in self.stringComparators]
			if self.variableComparatorCombo.currentText() == "is anything":
				self.variableValue.setText("")
				self.variableValue.setEnabled(False)
			else:
				self.variableValue.setEnabled(True)
		elif varType == "Int" or varType == "Float":
			[self.variableComparatorCombo.addItem(x) for x in self.numericComparators]
			self.variableValue.setEnabled(True)
		elif varType == "Boolean":
			[self.variableComparatorCombo.addItem(x) for x in self.boolComparators]
			self.variableValue.setText("")
			self.variableValue.setEnabled(False)
	
	def variableComparatorChanged(self):
		comboVal = self.variableComparatorCombo.currentText()
		if self.variableType.text() == "Boolean":
			self.variableValue.setText("")
			self.variableValue.setEnabled(False)
		else:
			if comboVal == "is anything":
				self.variableValue.setText("")
				self.variableValue.setEnabled(False)
			else:
				self.variableValue.setEnabled(True)
	
	def speechComparatorChanged(self):
		comboVal = self.speechComparatorCombo.currentText()
		if comboVal == "is anything":
			self.speechValueEntry.setText("")
			self.speechValueEntry.setEnabled(False)
		else:
			self.speechValueEntry.setEnabled(True)
	
	def mergeConditions(self):
		selectedIndexes = [x.row() for x in self.conditionList.selectedIndexes()]		
		targetConditions = [x for ind, x in enumerate(self.conditions) if ind in selectedIndexes]
		multiCond = MultiCondition()
		for c in targetConditions:
			multiCond.addConditions(c)

		#multicondition already exists
		if multiCond in self.conditions:
			msgBox = QMessageBox()
			msgBox.setText("Condition already exists!")
			msgBox.exec()
			return
		
		self.conditions[selectedIndexes[0]] = multiCond
		self.conditions = [c for ind, c in enumerate(self.conditions) if ind not in selectedIndexes[1:]]
		self.refreshConditions()
		self.selectIndexOfConditionList(min(selectedIndexes))

	
	def editValue(self):
		selectedIndex = self.conditionList.selectedIndexes()[0].row()
		selectedCondition = self.conditions[selectedIndex]
		if isinstance(selectedCondition, Condition):
			dlg = EditValueWindow(selectedCondition)
			accept = dlg.exec()
			newValue = dlg.edit.text()
			if accept and isConditionValid(selectedCondition.comparator, newValue, selectedCondition.targetType):
				selectedCondition.compareValue = newValue
		elif isinstance(selectedCondition, MultiCondition):
			dlg = EditMultiConditionWindow(selectedCondition)
			accept = dlg.exec()
			if accept:
				for ind, c in enumerate(selectedCondition.conditions):
					newValue = dlg.entries[ind].text()
					if isConditionValid(c.comparator, newValue, c.targetType):
						c.compareValue = dlg.entries[ind].text()
		self.refreshConditions()
		self.selectIndexOfConditionList(selectedIndex)


	def listSelectionChanged(self):
		numSelected = len(self.conditionList.selectedIndexes())
		if numSelected == 0:
			self.disableButtons()
		elif numSelected == 1:
			selectedIndex = self.conditionList.selectedIndexes()[0].row()
			self.combineButton.setEnabled(False)
			self.editValueButton.setEnabled(True)
			if selectedIndex == 0:
				self.moveUpButton.setEnabled(False)
				if selectedIndex == self.itemModel.rowCount() - 1:
					self.moveDownButton.setEnabled(False)
				else:
					self.moveDownButton.setEnabled(True)
				self.removeConditionButton.setEnabled(True)
			elif selectedIndex == self.itemModel.rowCount() - 1:
				self.moveUpButton.setEnabled(True)
				self.moveDownButton.setEnabled(False)
				self.removeConditionButton.setEnabled(True)		
			else:
				self.moveUpButton.setEnabled(True)
				self.moveDownButton.setEnabled(True)
				self.removeConditionButton.setEnabled(True)		
		elif numSelected >= 2:
			self.moveUpButton.setEnabled(False)
			self.moveDownButton.setEnabled(False)
			self.editValueButton.setEnabled(False)
			self.combineButton.setEnabled(True)
			self.removeConditionButton.setEnabled(True)
		

	
	def disableButtons(self):
		self.moveUpButton.setEnabled(False)
		self.moveDownButton.setEnabled(False)
		self.combineButton.setEnabled(False)
		self.editValueButton.setEnabled(False)
		self.removeConditionButton.setEnabled(False)
	
	def addSpeechCondition(self):
		obj = self.speechObjectCombo.currentText()
		val = self.speechValueEntry.text().strip()
		comp = self.speechComparatorCombo.currentText()
		varType = "String" if ("character length" not in comp and "word length" not in comp) else "Int"

		if not isConditionValid(comp, val, varType):
			return
	
		cond = Condition()
		cond.updateCondition(obj, comp, val, varType)

		#condition already exists
		if cond in self.conditions:
			msgBox = QMessageBox()
			msgBox.setText("Condition already exists!")
			msgBox.exec()
			return False
		
		self.conditions.append(cond)
		self.refreshConditions()
		self.speechValueEntry.setText("")
		self.disableButtons()
	
	def addListCondition(self):
		obj = self.listObjectCombo.currentText()
		val = "Wordlist(" + self.listValueEntry.currentText() + ")"
		comp = self.listComparatorCombo.currentText()
		varType = "String"

		if not isConditionValid(comp, val, varType):
			return
		
		cond = Condition()
		cond.updateCondition(obj, comp, val, varType)

		#condition already exists
		if cond in self.conditions:
			msgBox = QMessageBox()
			msgBox.setText("Condition already exists!")
			msgBox.exec()
			return False
		
		self.conditions.append(cond)
		self.refreshConditions()
	
	def addVariableCondition(self):
		obj = "Variable(" + self.variableCombo.currentText() + ")"
		val = self.variableValue.text().strip()
		comp = self.variableComparatorCombo.currentText()
		varType = self.variableType.text()

		if not isConditionValid(comp, val, varType):
			return
	
		cond = Condition()
		if varType == "Boolean":
			#adjust this because the user chooses the comparator...
			cond.updateCondition(obj, "is", comp, varType)
		else:
			cond.updateCondition(obj, comp, val, varType)

		#condition already exists
		if cond in self.conditions:
			msgBox = QMessageBox()
			msgBox.setText("Condition already exists!")
			msgBox.exec()
			return
		
		self.conditions.append(cond)
		self.refreshConditions()
		self.disableButtons()
		
	
	def removeCondition(self):
		selectedIndexes = [x.row() for x in self.conditionList.selectedIndexes()]		
		self.conditions = [x for ind, x in enumerate(self.conditions) if ind not in selectedIndexes]
		self.refreshConditions()
		self.disableButtons()

	
	def moveConditionUp(self):
		if len(self.conditionList.selectedIndexes()) != 1:
			return
		selectedIndex = self.conditionList.selectedIndexes()[0].row()
		self.conditions.insert(selectedIndex - 1, self.conditions.pop(selectedIndex))
		self.refreshConditions()
		self.selectIndexOfConditionList(selectedIndex - 1)
	
	def moveConditionDown(self):
		if len(self.conditionList.selectedIndexes()) != 1:
			return
		selectedIndex = self.conditionList.selectedIndexes()[0].row()
		self.conditions.insert(selectedIndex + 1, self.conditions.pop(selectedIndex))
		self.refreshConditions()
		self.selectIndexOfConditionList(selectedIndex + 1)

	
	def selectIndexOfConditionList(self, index):
		self.conditionList.selectionModel().select(self.itemModel.index(index, 0), QtCore.QItemSelectionModel.Select)

	
	def refreshConditions(self):
		self.itemModel.clear()

		for cond in self.conditions:
			c = QStandardItem(cond.displayString())
			self.itemModel.appendRow(c)
		
		if self.silenceCondition != None:
			self.silenceValue.setValue(self.silenceCondition.compareValue)
			self.silenceValue.setEnabled(True)
			self.silenceLabel.setEnabled(True)
			self.silenceCheck.setChecked(True)
		else:
			self.silenceValue.setEnabled(False)
			self.silenceLabel.setEnabled(False)
			self.silenceCheck.setChecked(False)
		
		if self.timerCondition != None:
			self.timerCheck.setChecked(True)



class EditValueWindow(QDialog):
	def __init__(self, condition):
		super().__init__()
		self.setWindowTitle("Edit value")
		layout = QVBoxLayout()

		dataEntryLayout = QHBoxLayout()
		dataEntryLayout.addWidget(QLabel(condition.targetObject))
		dataEntryLayout.addWidget(QLabel(condition.comparator))
		self.edit = QLineEdit()
		self.edit.setText(condition.compareValue)
		if condition.comparator.strip() == "is anything":
			self.edit.setEnabled(False)
		dataEntryLayout.addWidget(self.edit)

		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)
	
		layout.addLayout(dataEntryLayout)
		layout.addWidget(confirmButtons)

		self.setLayout(layout)

class EditMultiConditionWindow(QDialog):
	def __init__(self, condition):
		super().__init__()
		self.setWindowTitle("Edit value")
		layout = QVBoxLayout()
		self.entries = []

		for c in condition.conditions:
			dataEntryLayout = QHBoxLayout()
			dataEntryLayout.addWidget(QLabel(c.targetObject))
			dataEntryLayout.addWidget(QLabel(c.comparator))
			edit = QLineEdit()
			edit.setText(c.compareValue)
			self.entries.append(edit)
			if c.comparator.strip() == "is anything":
				edit.setEnabled(False)
			dataEntryLayout.addWidget(edit)
			layout.addLayout(dataEntryLayout)

		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		layout.addWidget(confirmButtons)

		self.setLayout(layout)

class HumanTargetWindow(QDialog):
	def __init__(self, initial_target, environment):
		super().__init__()	

		self.setWindowTitle("Set the target human")

		layout = QVBoxLayout()
		childLayout = QHBoxLayout()
		self.chooser = QComboBox()
		for user in environment:
			self.chooser.addItem("Human " + str(user[0]))
		self.chooser.addItems(["None", "Non-target random", "Any random"])
		if initial_target != None:
			self.chooser.setCurrentText(initial_target)

		childLayout.addWidget(QLabel("Choose target human"))
		childLayout.addWidget(self.chooser)
		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		layout.addLayout(childLayout)
		layout.addWidget(confirmButtons)

		self.setLayout(layout)