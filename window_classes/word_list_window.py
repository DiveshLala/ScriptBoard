from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QPushButton, QComboBox, QAbstractItemView, QListView, QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from pathvalidate import ValidationError, validate_filename

import os

class WordListWindow(QDialog):

	def __init__(self, parentWindow):
		super().__init__()
		self.setWindowTitle("Word Lists")


		listChooserLayout = QHBoxLayout()
		self.wordListCombo = QComboBox()
		self.wordListCombo.setFixedWidth(300)

		for x in os.listdir("./word_lists"):
			if x.endswith(".words"):
				self.wordListCombo.addItem(x.replace(".words", ""))

		newButton = QPushButton("New List")
		newButton.clicked.connect(self.createList)
		listChooserLayout.addWidget(self.wordListCombo)
		listChooserLayout.addWidget(newButton)
		
		displayLayout = QHBoxLayout()
		self.wordList = QListView()
		self.wordList.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.itemModel = QStandardItemModel()
		self.wordList.setModel(self.itemModel)
		self.wordList.selectionModel().selectionChanged.connect(self.listSelectionChanged)

		self.removeButton = QPushButton("Remove word")
		self.removeButton.setEnabled(False)
		self.removeButton.clicked.connect(self.removeWord)
		displayLayout.addWidget(self.wordList)
		displayLayout.addWidget(self.removeButton)

		addWordLayout = QHBoxLayout()
		self.wordEntry = QLineEdit()
		self.wordEntry.setFixedWidth(300)
		addButton = QPushButton("Add word")
		addButton.clicked.connect(self.addWord)

		addWordLayout.addWidget(self.wordEntry)
		addWordLayout.addWidget(addButton)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("List"))
		layout.addLayout(listChooserLayout)
		layout.addLayout(displayLayout)
		layout.addLayout(addWordLayout)
		self.setLayout(layout)

		self.wordListCombo.currentIndexChanged.connect(self.update_word_list)
		self.update_word_list()
	
	def update_word_list(self):
		self.itemModel.clear()
		x = self.wordListCombo.currentText()
		if len(x) > 0:
			file = open("./word_lists/" + x + ".words", "r", encoding="utf-8")
			for word in file.readlines():
				if len(word) > 0:
					self.itemModel.appendRow(QStandardItem(word.strip()))
		self.removeButton.setEnabled(False)
	
	def listSelectionChanged(self):
		self.removeButton.setEnabled(True)
	
	def removeWord(self):
		index = self.wordList.selectedIndexes()[0].row()
		try:
			file = open("./word_lists/" + self.wordListCombo.currentText() + ".words", "r", encoding="utf-8")
			words = file.readlines()
			words.remove(words[index])
			file = open("./word_lists/" + self.wordListCombo.currentText() + ".words", "w", encoding="utf-8")
			for x in words:
				file.write(x)
			file.close()
			self.update_word_list()
		except FileNotFoundError:
			print("No such file?")
	
	def addWord(self):

		if len(self.wordEntry.text().strip()) == 0:
			return

		try:
			file = open("./word_lists/" + self.wordListCombo.currentText() + ".words", "a", encoding="utf-8")
			file.write(self.wordEntry.text().strip() + "\n")
			file.close()
			self.update_word_list()
			self.wordEntry.clear()
		except FileNotFoundError:
			print("No such file?")
	
	def createList(self):

		newList = NewListWindow()
		newList.exec()

		if newList.newfile != None:
			with open("./word_lists/" + newList.newfile + ".words", 'w') as fp:
				print("created")
				self.wordListCombo.addItem(newList.newfile)
				self.wordListCombo.setCurrentText(newList.newfile)
	
		self.update_word_list()	
		self.wordEntry.clear()


class NewListWindow(QDialog):

	def __init__(self):
		super().__init__()
		self.setWindowTitle("Name of new word list")
		self.newfile = None
		layout = QVBoxLayout()
		layout.addWidget(QLabel("Set name of word list"))
		self.entry = QLineEdit()
		layout.addWidget(self.entry)
		createButton = QPushButton("Create list")
		createButton.clicked.connect(self.createList)
		layout.addWidget(createButton)
		self.setLayout(layout)
	

	def createList(self):
		newfile = self.entry.text()
		msg = isvalid(newfile)
		if msg == -1:
			msgBox = QMessageBox()
			msgBox.setText("Please specify a valid file name!")
			msgBox.exec()
		elif msg == -2:
			msgBox = QMessageBox()
			msgBox.setText("This word list already exists!")
			msgBox.exec()
		else:
			self.newfile = newfile
			self.close()

def isvalid(filename):

	try:
		validate_filename(filename)
	except ValidationError:
		return -1

	for x in os.listdir("./word_lists"):
		if x.replace(".words", "").strip() == filename:
			return -2
	return 0

		




	

