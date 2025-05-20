from PyQt5.QtWidgets import QListView, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QPushButton, QAbstractItemView, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from condition import Condition


class TurnStateDecisionWindow(QDialog):

	def __init__(self, initConditions):
		super(TurnStateDecisionWindow, self).__init__()

		self.setWindowTitle("Turn-state Decision")
		self.conditions = []

		#variable selection
		layout = QVBoxLayout()
		chooserLayout = QHBoxLayout()
		self.turnStateCombo = QComboBox()
		self.turnStateCombo.addItems(["Offer to human", "Human", "Offer to robot", "Robot"])
		self.turnStateCombo.setFixedWidth(300)
		self.addConditionButton = QPushButton("Add")
		self.addConditionButton.clicked.connect(self.addCondition)

		chooserLayout.addWidget(self.turnStateCombo)
		chooserLayout.addWidget(self.addConditionButton)


		# #condition list
		self.conditionList = QListView()
		self.conditionList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.itemModel = QStandardItemModel()
		self.conditionList.setModel(self.itemModel)
		self.conditionList.setFixedWidth(300)

		conditionListLayout = QHBoxLayout()
		listModLayout = QVBoxLayout()
		self.removeConditionButton = QPushButton("Remove")
		self.removeConditionButton.clicked.connect(self.removeCondition)

		listModLayout.addWidget(self.removeConditionButton)
		conditionListLayout.addWidget(self.conditionList)
		conditionListLayout.addLayout(listModLayout)

		#ok cancel buttons
		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Turn states"))
		layout.addLayout(chooserLayout)
		layout.addLayout(conditionListLayout)
		layout.addWidget(confirmButtons)
		self.setLayout(layout)

		if len(initConditions) > 0:
			for cond in initConditions:
				self.conditions.append(cond)
				turnState = cond.compareValue
				self.turnStateCombo.removeItem(self.turnStateCombo.findText(turnState))
			self.refreshConditions()
		if self.turnStateCombo.count() == 0:
			self.addConditionButton.setEnabled(False)
	
	def refreshConditions(self):
		self.itemModel.clear()

		for cond in self.conditions:
			c = QStandardItem(cond.displayString())
			self.itemModel.appendRow(c)
		
	def addCondition(self):
		turnState = self.turnStateCombo.currentText()
		cond = Condition()
		cond.updateCondition("Turn state", "is", turnState, "String")
		self.conditions.append(cond)
		self.refreshConditions()
		self.turnStateCombo.removeItem(self.turnStateCombo.currentIndex())
		if self.turnStateCombo.count() == 0:
			self.addConditionButton.setEnabled(False)
	
	def removeCondition(self):
		selectedIndexes = [x.row() for x in self.conditionList.selectedIndexes()]
		if len(selectedIndexes) == 0:
			return	
		i = self.conditionList.currentIndex()
		turnState = self.itemModel.itemFromIndex(i).text().split(" is ")[-1]
		self.conditions = [x for ind, x in enumerate(self.conditions) if ind not in selectedIndexes]
		self.refreshConditions()
		self.turnStateCombo.addItems([turnState])
		if self.turnStateCombo.count() > 0:
			self.addConditionButton.setEnabled(True)