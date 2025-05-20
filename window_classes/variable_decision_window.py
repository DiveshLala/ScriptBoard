from PyQt5.QtWidgets import QListView, QDialogButtonBox, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QPushButton, QAbstractItemView, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from condition import Condition
from condition import isConditionValid
from script_processor import get_string_between_brackets

class VariableDecisionWindow(QDialog):

	def __init__(self, initConditions, variables):
		super(VariableDecisionWindow, self).__init__()

		self.setWindowTitle("Variable Decision")
		self.conditions = []
		self.variables = variables

		#variable selection
		layout = QVBoxLayout()
		variableSelectionLayout = QHBoxLayout()
		self.variableCombo = QComboBox()
		self.variableCombo.addItems([x[0] for x in self.variables])
		self.variableCombo.currentIndexChanged.connect(self.selectedVariableChanged)
		self.variableType = QLabel()
		variableSelectionLayout.addWidget(self.variableCombo)
		variableSelectionLayout.addWidget(self.variableType)

		#condition list
		self.conditionList = QListView()
		self.conditionList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.conditionList.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.itemModel = QStandardItemModel()
		self.conditionList.setModel(self.itemModel)

		conditionListLayout = QHBoxLayout()
		listModLayout = QVBoxLayout()

		self.removeConditionButton = QPushButton("Remove")
		self.removeConditionButton.clicked.connect(self.removeCondition)

		listModLayout.addWidget(self.removeConditionButton)
		conditionListLayout.addWidget(self.conditionList)
		conditionListLayout.addLayout(listModLayout)

		#condition selection
		valueLayout = QHBoxLayout()
		self.comparatorCombo = QComboBox()
		self.comparatorCombo.setFixedWidth(250)
		self.comparatorCombo.currentIndexChanged.connect(self.variableComparatorChanged)
		self.variableValue = QLineEdit()
		addButton = QPushButton("Add")
		addButton.clicked.connect(self.addVariableCondition)
		valueLayout.addWidget(self.comparatorCombo)
		valueLayout.addWidget(self.variableValue)
		valueLayout.addWidget(addButton)

		#ok cancel buttons
		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Variable"))
		layout.addLayout(variableSelectionLayout)
		layout.addWidget(QLabel("Condition"))
		layout.addLayout(conditionListLayout)
		layout.addLayout(valueLayout)
		layout.addWidget(confirmButtons)
		self.setLayout(layout)

		self.currentVariableIndex = 0
		self.populateComboBoxes()

		if len(initConditions) > 0:
			for cond in initConditions:
				self.conditions.append(cond)
			self.refreshConditions()
			self.variableCombo.blockSignals(True)
			variableName = get_string_between_brackets(self.conditions[0].displayString())
			self.variableCombo.setCurrentText(variableName)
			self.currentVariableIndex = self.variableCombo.currentIndex()
			self.populateComboBoxes()
			self.variableCombo.blockSignals(False)


	def selectedVariableChanged(self):

		if self.itemModel.rowCount() > 0:
			dlg = QMessageBox()
			dlg.setWindowTitle("Change variable?")
			dlg.setText("Changing the variable will remove all conditions. Proceed?")
			dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			ret = dlg.exec()
			if ret == QMessageBox.No:
				self.variableCombo.blockSignals(True)
				self.variableCombo.setCurrentIndex(self.currentVariableIndex)
				self.variableCombo.blockSignals(False)
				return

		self.conditions = []
		self.refreshConditions()
		self.populateComboBoxes()
		self.currentVariableIndex = self.variableCombo.currentIndex()
	
	def variableComparatorChanged(self):
		comboVal = self.comparatorCombo.currentText()
		if self.variableType.text() == "Boolean":
			self.variableValue.setText("")
			self.variableValue.setEnabled(False)
		else:
			if comboVal == "is anything":
				self.variableValue.setText("")
				self.variableValue.setEnabled(False)
			else:
				self.variableValue.setEnabled(True)
	
	def populateComboBoxes(self):

		varTypes = [x[1] for x in self.variables]
		selectedType = varTypes[self.variableCombo.currentIndex()]
		self.variableType.setText(selectedType)

		stringComparators = ["equals", "contains", "contains word", "starts with", "ends with", "does not equal", "does not contain", "does not start with", "does not end with", "character length greater than", "character length less than"]
		numericComparators = ["=", ">", "<", ">=", "<="]
		boolComparators = ["true", "false"]

		self.comparatorCombo.clear()

		if selectedType == "String":
			self.comparatorCombo.addItems(stringComparators)
		elif selectedType == "Int" or selectedType == "Float":
			self.comparatorCombo.addItems(numericComparators)
		elif selectedType == "Boolean":
			self.comparatorCombo.addItems(boolComparators)
		self.variableValue.clear()

		

	def removeCondition(self):
		selectedIndexes = [x.row() for x in self.conditionList.selectedIndexes()]		
		self.conditions = [x for ind, x in enumerate(self.conditions) if ind not in selectedIndexes]
		self.refreshConditions()
	
	def refreshConditions(self):
		self.itemModel.clear()

		for cond in self.conditions:
			c = QStandardItem(cond.displayString())
			self.itemModel.appendRow(c)
	
	def addVariableCondition(self):
		obj = "Variable(" + self.variableCombo.currentText() + ")"
		val = self.variableValue.text().strip()
		comp = self.comparatorCombo.currentText()
		varType = self.variableType.text()

		if not isConditionValid(comp, val, varType):
			return
		
		if varType == "Boolean":
			val = comp
			comp = "is"
	
		cond = Condition()
		cond.updateCondition(obj, comp, val, varType)

		#condition already exists
		if cond in self.conditions:
			msgBox = QMessageBox()
			msgBox.setText("Condition already exists!")
			msgBox.exec()
			return
		
		self.conditions.append(cond)
		self.refreshConditions()