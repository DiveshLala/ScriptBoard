from PyQt5.QtWidgets import QDialogButtonBox, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QLineEdit, QComboBox, QSpinBox, QPushButton, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QFont

class TalkWindow(QDialog):
	def __init__(self, initInfo, environment, variables, bargeIn):
		super().__init__()

		self.setWindowTitle("Robot Dialogue")
		layout = QVBoxLayout()

		textLayout = QHBoxLayout()
		self.textBox = QTextEdit()
		self.textBox.setFixedWidth(400)
		self.setInitialText(initInfo[0])


		insertLayout = QVBoxLayout()
		self.variableCombo = QComboBox()
		self.variableCombo.addItems([x[0] for x in variables])
		self.insertButton = QPushButton("Insert variable")
		self.insertButton.clicked.connect(self.insertVariableString)
		insertLayout.addStretch(1)
		insertLayout.addWidget(self.variableCombo)
		insertLayout.addWidget(self.insertButton)
		insertLayout.addStretch(1)
		textLayout.addWidget(self.textBox)
		textLayout.addLayout(insertLayout)

		self.tag = QLineEdit()
		self.tag.setFixedWidth(200)
		self.tag.setText(initInfo[1])

		self.emotion = QLineEdit()
		self.emotion.setFixedWidth(200)
		self.emotion.setText(initInfo[2])

		self.gesture = QLineEdit()
		self.gesture.setFixedWidth(200)
		self.gesture.setText(initInfo[3])

		self.gazeCombo = QComboBox()
		self.gazeCombo.setFixedWidth(200)
		human_ids = [x[0] for x in environment]
		gazeItems = [""] + ["Human " + str(hid) for hid in human_ids] + ["Target", "No target", "Non-target first", "Non-target random", "Any random"]
		self.gazeCombo.addItems(gazeItems)
		try:
			self.gazeCombo.setCurrentIndex(gazeItems.index(initInfo[4]))
		except ValueError:
			self.gazeCombo.setCurrentIndex(0)

		bargeInLayout = QHBoxLayout()
		self.bargeInCheck = QCheckBox()
		self.bargeInCheck.setChecked(bargeIn)
		bargeInLayout.addWidget(QLabel("Handle barge-in?"))
		bargeInLayout.addWidget(self.bargeInCheck)
		bargeInLayout.addStretch(1)

		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Utterance"))
		layout.addLayout(textLayout)
		layout.addWidget(QLabel("Tag"))
		layout.addWidget(self.tag)
		layout.addWidget(QLabel("Emotion"))
		layout.addWidget(self.emotion)
		layout.addWidget(QLabel("Gesture"))
		layout.addWidget(self.gesture)
		layout.addWidget(QLabel("Gaze"))
		layout.addWidget(self.gazeCombo)
		layout.addLayout(bargeInLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)
	
	def insertVariableString(self):
		cursor = self.getCursor("Bold")
		self.insertText(cursor, "Variable(" + str(self.variableCombo.currentText()) + ")")
		#change back to regular cursor
		cursor = self.getCursor()
	
	def setInitialText(self, text):

		if len(text) == 0:
			return

		varStartIndices = [i for i in range(len(text)) if text.startswith("Variable(", i)]

		if len(varStartIndices) == 0:
			self.textBox.setText(text)
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


	def getCursor(self, type="Normal"):
		cursor = QTextCursor(self.textBox.textCursor())
		format = QTextCharFormat(cursor.charFormat())
		if type == "Bold":
			format.setFontWeight(QFont.Bold)
		else:
			format.setFontWeight(QFont.Normal)
		cursor.setCharFormat(format)
		self.textBox.setTextCursor(cursor)
		return cursor
	
	def insertText(self, cursor, text):
		self.textBox.moveCursor(QTextCursor.End)
		cursor.insertText(text)
		self.textBox.moveCursor(QTextCursor.End)
	



class TalkLLMWindow(QDialog):
	def __init__(self, initPrompt, initLabel, bargeIn, human_ids, variables, init_gaze):
		super().__init__()

		self.setWindowTitle("LLM Dialogue")
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
		self.variableCombo = QComboBox()
		self.variableCombo.addItems([x for x in variables])
		self.insertButton = QPushButton("Insert variable")
		self.insertButton.clicked.connect(self.insertVariableString)
		insertLayout.addStretch(1)
		insertLayout.addWidget(self.variableCombo)
		insertLayout.addWidget(self.insertButton)
		insertLayout.addStretch(1)
		promptLayout.addWidget(self.promptBox)
		promptLayout.addLayout(insertLayout)

		self.participantCombo = QComboBox()
		self.participantCombo.setFixedWidth(300)
		self.participantCombo.addItems(["None", "All", "Users only", "Target user only", "Non-target user only", "Robot only", "Target and Robot only"])
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

		self.gazeCombo = QComboBox()
		self.gazeCombo.setFixedWidth(200)
		gazeItems = [""] + ["Human " + str(hid) for hid in human_ids] + ["Target", "No target", "Non-target first", "Non-target random", "Any random", "Multiparty shift"]
		self.gazeCombo.addItems(gazeItems)
		try:
			self.gazeCombo.setCurrentIndex(gazeItems.index(init_gaze))
		except ValueError:
			self.gazeCombo.setCurrentIndex(0)

		bargeInLayout = QHBoxLayout()
		self.bargeInCheck = QCheckBox()
		self.bargeInCheck.setChecked(bargeIn)
		bargeInLayout.addWidget(QLabel("Handle barge-in?"))
		bargeInLayout.addWidget(self.bargeInCheck)
		bargeInLayout.addStretch(1)

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
		layout.addWidget(QLabel("Gaze behavior for response"))
		layout.addWidget(self.gazeCombo)
		layout.addLayout(bargeInLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)

		if len(initSpeakers) > 0:
			self.participantCombo.setCurrentText(initSpeakers) 
		
		if len(initHistory) > 0:
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
	
	def insertVariableString(self):
		cursor = self.getCursor("Bold")
		self.insertText(cursor, "Variable(" + str(self.variableCombo.currentText()) + ")")
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