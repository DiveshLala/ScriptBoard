from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QLabel, QDialog, QPushButton
from PyQt5 import QtCore
from llm.LLM_API_server import check_for_GPT, check_for_Gemini, check_for_LMStudio
import time

class LLMListWindow(QDialog):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("List of LLMs")

		self.LLMList = QTableWidget(0, 3)
		self.LLMList.setHorizontalHeaderLabels(["LLM", "", "Status",])
		self.LLMList.setFixedWidth(400)

		self.loadLLMList()

		self.messageLabel = QLabel("")

		layout = QVBoxLayout()
		layout.addWidget(QLabel("LLM list"))
		layout.addWidget(self.LLMList)
		layout.addWidget(self.messageLabel)

		self.setLayout(layout)
	
	def loadLLMList(self):
		LLMs = ["GPT", "Gemini", "LM Studio"]
		rowCt = 0
		for llm in LLMs:
			self.LLMList.insertRow(rowCt)

			name = QTableWidgetItem(llm)
			self.LLMList.setItem(rowCt, 0, name)
			name.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)

			LLMCheckButton = QPushButton("Check status")
			LLMCheckButton.setObjectName(str(llm))
			self.LLMList.setCellWidget(rowCt, 1, LLMCheckButton)
			LLMCheckButton.clicked.connect(self.checkChanged)

			status = QTableWidgetItem("")
			self.LLMList.setItem(rowCt, 2, status)
			status.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
		
			rowCt += 1
	
	def checkChanged(self):
		llm = self.sender().objectName()

		for i in range(self.LLMList.rowCount()):
			if self.LLMList.item(i, 0).text() == llm:
				self.updateStatus(llm, i)
	
	def updateStatus(self, llm, index):

		status = QTableWidgetItem("Waiting...")
		self.LLMList.setItem(index, 2, status)
		self.LLMList.setEnabled(False)

		if llm == "GPT":
			available = check_for_GPT()		
		elif llm == "Gemini":
			available = check_for_Gemini()
		elif llm == "LM Studio":
			available = check_for_LMStudio()
			
		if available == -1:
			self.messageLabel.setText("Python packages are not installed. Use pip to install.")
			status = QTableWidgetItem("Not available")
		elif available == -2:
			self.messageLabel.setText("Configuration file does not exist. Create a file named llm/llm_login_info.txt")
			status = QTableWidgetItem("Not available")
		elif available == -3:
			self.messageLabel.setText("Configuration file not formatted properly.  Please check llm/llm_login_info_example.txt")
			status = QTableWidgetItem("Not available")
		elif available == -4:
			self.messageLabel.setText("API details are incorrect.  Please check your configuration file.")
			status = QTableWidgetItem("Not available")
		elif available == -5:
			self.messageLabel.setText("LM Studio server is not running. Please load a model inside the application.")
			status = QTableWidgetItem("Not available")
		else:
			self.messageLabel.setText("")	
			status = QTableWidgetItem("Available")

		self.LLMList.setEnabled(True)
		self.LLMList.setItem(index, 2, status)
		status.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
	
		