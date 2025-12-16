from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QLabel, QDialog, QComboBox, QTextEdit, QCheckBox, QHBoxLayout, QSpinBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import time
import threading
import json

class SimulationWindow(QDialog):
	def __init__(self, parent, humanIDs):
		super().__init__()

		self.parent = parent
		
		self.setWindowTitle("Enter manual speech recognition")
		self.setWindowFlag(Qt.WindowCloseButtonHint, False)
		
		layout = QVBoxLayout()
		layout.addWidget(QLabel("Human"))
		
		self.humanCombo = QComboBox()
		for x in humanIDs:
			self.humanCombo.addItem(str(x))
		layout.addWidget(self.humanCombo)

		layout.addWidget(QLabel("ASR text to simulate"))
		self.manualEntry = QTextEdit()
		self.manualEntry.setFixedWidth(400)
		self.manualEntry.setFixedHeight(100)
		self.manualEntry.textChanged.connect(self.textChanged)
		layout.addWidget(self.manualEntry)

		turnLayout = QHBoxLayout()
		self.turnTime = QSpinBox()
		self.turnTime.setRange(0, 5000)
		self.turnTime.setSingleStep(500)
		self.turnTime.setValue(1000)
		turnLayout.addWidget(QLabel("Time taken for robot turn"))
		turnLayout.addWidget(self.turnTime)
		layout.addLayout(turnLayout)

		layout.addWidget(QLabel("Conversation History:"))
		self.conversationHistory = QTextEdit()
		self.conversationHistory.setFixedWidth(400)
		self.conversationHistory.setFixedHeight(300)
		self.conversationHistory.setReadOnly(True)
		font = QFont()
		font.setPointSize(12)
		self.conversationHistory.setFont(font)
		layout.addWidget(self.conversationHistory)

		self.confirm = QPushButton("Simulate")
		self.confirm.clicked.connect(self.simulateASR)
		self.confirm.setEnabled(False)
		layout.addWidget(self.confirm)

		self.setLayout(layout)

		self.dialogState = DialogState(parent, self)
	
	def simulateASR(self):
		speaker = int(self.humanCombo.currentText())
		utterance = self.manualEntry.toPlainText().strip()
		self.dialogState.sendASR(speaker, utterance)
		self.manualEntry.clear()
		self.conversationHistory.append("Human " + str(speaker) + ": " + utterance)

	
	def textChanged(self):
		if self.dialogState != "ROBOT_TURN" and self.dialogState != "OFFER_TO_ROBOT":
			if len(self.manualEntry.toPlainText().strip()) > 0:
				self.dialogState.human_speaking(True, self.humanCombo.currentText())
				self.confirm.setEnabled(True)
			else:
				self.dialogState.human_speaking(False, self.humanCombo.currentText())
				self.confirm.setEnabled(False)

	def receiveMessage(self, message):
		self.dialogState.receive_message(message)


class DialogState:
	def __init__(self, parent, simWindow):
		self.parent = parent
		self.simWindow = simWindow
		self.turn_state = None
		self.silence_time_start = 0
		self.user_speaking = False
		
		silenceThread = threading.Thread(target=self.check_for_silence)
		silenceThread.daemon = True
		silenceThread.start()
	
	def check_for_silence(self):
		while True:
			if self.turn_state == "HUMAN_TURN" and not self.user_speaking:
				if (time.time() - self.silence_time_start) * 1000 >= self.simWindow.turnTime.value():
					self.update_turn_state(None, "OFFER_TO_ROBOT")
			time.sleep(0.02)
	
	def human_speaking(self, is_speaking, human_id):
		self.user_speaking = is_speaking
		if is_speaking:
			if self.turn_state != "HUMAN_TURN":
				self.update_turn_state(human_id, "HUMAN_TURN")
		
	def sendASR(self, speaker, utterance):
		self.parent.sendSimulatedASRMessage(speaker, utterance)
		self.silence_time_start = time.time()
		self.user_speaking = False
	
	def update_turn_state(self, human_id, t):
		if self.turn_state != t and not(self.turn_state == "ROBOT_TURN" and t == "HUMAN_TURN"):
			self.turn_state = t
			self.parent.sendSimulatedTurnMessage(human_id, t)
	
	def receive_message(self, message):
		msg_obj = json.loads(message)
		if msg_obj.get("type") == "robot utterance":
			utterance = msg_obj.get("utterance")
			self.update_turn_state(None, "ROBOT_TURN")
			self.simWindow.confirm.setEnabled(False)
			self.silence_time_start = time.time()
			self.simWindow.conversationHistory.append("Robot: " + utterance)
			time.sleep(1)
			self.silence_time_start = time.time()
			self.parent.sendSimulatedRobotSpeechMessage(utterance)
			self.update_turn_state(None, "OFFER_TO_HUMAN")





