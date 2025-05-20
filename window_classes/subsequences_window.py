from PyQt5.QtWidgets import QListView, QDialogButtonBox, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QPushButton, QAbstractItemView, QComboBox
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class SubsequencesWindow(QDialog):
	def __init__(self, initSequences):
		super().__init__()
		self.setWindowTitle("Subsequences")
		self.subsequences = []
		for x in initSequences:
			self.subsequences.append(x)
		listLayout = QHBoxLayout()
		self.subsequenceList = QListView()
		self.itemModel = QStandardItemModel()
		self.subsequenceList.setModel(self.itemModel)
		self.subsequenceList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.removeButton = QPushButton("Remove")
		self.removeButton.clicked.connect(self.removeSubsequence)
		self.refreshList()
		listLayout.addWidget(self.subsequenceList)
		listLayout.addWidget(self.removeButton)

		addLayout = QHBoxLayout()
		self.entry = QLineEdit()
		addButton = QPushButton("Add")
		addButton.clicked.connect(self.addSubsequence)
		addLayout.addWidget(self.entry)
		addLayout.addWidget(addButton)

		#ok cancel buttons
		confirmButtons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		confirmButtons.accepted.connect(self.accept)
		confirmButtons.rejected.connect(self.reject)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("List of subsequences"))
		layout.addLayout(listLayout)
		layout.addLayout(addLayout)
		layout.addWidget(confirmButtons)

		self.setLayout(layout)
	
	def addSubsequence(self):
		if len(self.entry.text()) == 0:
			return
	
		if self.entry.text().strip() in self.subsequences:
			msgBox = QMessageBox()
			msgBox.setText("This subsequence already exists!")
			msgBox.exec()
			return
	
		self.subsequences.append(self.entry.text())
		self.refreshList()
	
	def removeSubsequence(self):
		selectedIndexes = [x.row() for x in self.subsequenceList.selectedIndexes()]		
		self.subsequences = [x for ind, x in enumerate(self.subsequences) if ind not in selectedIndexes]
		self.refreshList()

	
	def refreshList(self):
		self.itemModel.clear()
		for x in self.subsequences:
			c = QStandardItem(x)
			self.itemModel.appendRow(c)
			
		if self.subsequenceList.model().rowCount() > 0:
			self.subsequenceList.selectionModel().select(self.itemModel.index(0, 0), QtCore.QItemSelectionModel.Select)
			self.removeButton.setEnabled(True)
		else:
			self.removeButton.setEnabled(False)


class EnterSubsequenceWindow(QDialog):
	def __init__(self, subsequences, initSubseq):
		super().__init__()

		self.setWindowTitle("Run subsequence")
		layout = QVBoxLayout()

		self.subsequenceCombo = QComboBox()
		self.subsequenceCombo.addItems(subsequences)

		if len(initSubseq) > 0:
			self.subsequenceCombo.setCurrentText(initSubseq)
		
		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Choose the subsequence to run:"))
		layout.addWidget(self.subsequenceCombo)
		layout.addWidget(buttons)
		self.setLayout(layout)
