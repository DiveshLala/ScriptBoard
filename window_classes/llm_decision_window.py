from PyQt5.QtWidgets import QMessageBox, QDialogButtonBox, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QComboBox, QSpinBox, QListView, QAbstractItemView, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from condition import Condition, isConditionValid


class LLMDecisionWindow(QDialog):
	def __init__(self, initPrompt, initLabel, initConditions):
		super().__init__()

		self.setWindowTitle("LLM Decision")
		layout = QVBoxLayout()

		self.conditions = []

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

		self.promptBox = QTextEdit()
		self.promptBox.setFixedHeight(300)
		self.promptBox.setFixedWidth(800)
		self.promptBox.setText(initPromptText)

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

		conditionListLayout = QHBoxLayout()
		self.conditionList = QListView()
		self.conditionList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.conditionList.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.silenceCondition = None
		self.itemModel = QStandardItemModel()
		self.conditionList.setModel(self.itemModel)
		self.conditionList.selectionModel().selectionChanged.connect(self.listSelectionChanged)


		self.removeButton = QPushButton("Remove")
		self.removeButton.setEnabled(False)
		self.removeButton.clicked.connect(self.removeCondition)
		conditionListLayout.addWidget(self.conditionList)
		conditionListLayout.addWidget(self.removeButton)

		for cond in initConditions:
			self.conditions.append(cond)
		self.refreshConditions()
		
		conditionLayout = QHBoxLayout()
		self.typeCombo = QComboBox()
		self.typeCombo.setFixedWidth(150)
		self.typeCombo.addItems(["String", "Numeric"])
		self.typeCombo.currentIndexChanged.connect(self.changeTypeCombo)
		
		self.comparatorCombo = QComboBox()
		self.comparatorCombo.setFixedWidth(150)
		self.stringComparators = ["equals", "contains", "contains word", "starts with"]
		self.numericComparators = ["=", ">", "<"]
		self.comparatorCombo.addItems(self.stringComparators)
		
		self.valueBox = QLineEdit()
		self.valueBox.setFixedWidth(200)

		self.addButton = QPushButton("Add")
		self.addButton.setFixedWidth(100)
		self.addButton.clicked.connect(self.addCondition)
		
		conditionLayout.addWidget(self.typeCombo)
		conditionLayout.addWidget(self.comparatorCombo)
		conditionLayout.addWidget(self.valueBox)
		conditionLayout.addStretch(1)
		conditionLayout.addWidget(self.addButton)


		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Label"))
		layout.addWidget(self.label)
		layout.addWidget(QLabel("Prompt"))
		layout.addWidget(self.promptBox)
		layout.addWidget(QLabel("Information to be added below prompt"))
		layout.addWidget(QLabel("Whose utterances to add?"))
		layout.addWidget(self.participantCombo)
		layout.addWidget(QLabel("Which dialog to add?"))
		layout.addWidget(self.contextCombo)
		layout.addWidget(QLabel("Maximum number of turns to be added"))
		layout.addWidget(self.numTurns)
		layout.addWidget(QLabel("List of conditions"))
		layout.addLayout(conditionListLayout)
		layout.addWidget(QLabel("Conditions to add (all conditions must be of the same type)"))
		layout.addLayout(conditionLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)

		if len(initSpeakers) > 0 and len(initSpeakers) > 0:
			self.participantCombo.setCurrentText(initSpeakers) 
		
		if len(initHistory) > 0 and len(initHistory) > 0:
			self.contextCombo.setCurrentText(initHistory)
		
		if initTurns > 0:
			self.numTurns.setValue(initTurns)

		self.changeContextCombo()
		self.changeParticipantCombo()


	def changeParticipantCombo(self):
		self.contextCombo.setEnabled(self.participantCombo.currentText() != "None")
		if self.participantCombo.currentText() == "None":
			self.numTurns.setEnabled(False)
		else:
			self.changeContextCombo()

	def changeContextCombo(self):
		self.numTurns.setEnabled(self.contextCombo.currentText() != "Whole dialog history")
	
	def changeTypeCombo(self):
		if self.itemModel.rowCount() > 0:
			dlg = QMessageBox()
			dlg.setWindowTitle("Change the output type?")
			dlg.setText("Changing the type of output will clear all conditions. Proceed?")
			dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			ret = dlg.exec()
			if ret == QMessageBox.No:
				return

		self.conditions = []
		self.comparatorCombo.clear()
		self.valueBox.clear()
		if self.typeCombo.currentText() == "String":
			self.comparatorCombo.addItems(self.stringComparators)
		else:
			self.comparatorCombo.addItems(self.numericComparators)
		self.refreshConditions()
	
	def addCondition(self):
		if len(self.valueBox.text()) == 0:
			msgBox = QMessageBox()
			msgBox.setText("Must enter a value!")
			msgBox.exec()
			return

		if self.typeCombo.currentText() == "Numeric" and not isConditionValid(self.comparatorCombo.currentText(), self.valueBox.text(), "Float"):
			return

		cond = Condition()
		cond.updateCondition("LLM output", self.comparatorCombo.currentText(), self.valueBox.text(), self.typeCombo.currentText())
		self.conditions.append(cond)
		self.refreshConditions()

	def removeCondition(self):
		selectedIndexes = [x.row() for x in self.conditionList.selectedIndexes()]		
		self.conditions = [x for ind, x in enumerate(self.conditions) if ind not in selectedIndexes]
		self.refreshConditions()
		self.removeButton.setEnabled(False)
	
	def listSelectionChanged(self):
		self.removeButton.setEnabled(True)

	def refreshConditions(self):
		self.itemModel.clear()

		for cond in self.conditions:
			c = QStandardItem(cond.displayString())
			self.itemModel.appendRow(c)
		
		if self.itemModel.rowCount() == 0:
			self.removeButton.setEnabled(False)
