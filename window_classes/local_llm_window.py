from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QLabel, QDialog, QPushButton, QHBoxLayout, QLineEdit, QComboBox, QMessageBox
from PyQt5 import QtCore
from llm.LLM_API_server import check_for_GPT, check_for_Gemini, check_for_LMStudio
import time

class LocalLLMWindow(QDialog):
	def __init__(self, initSettings, scene):
		super().__init__()

		self.parentScene = scene

		self.setWindowTitle("Local LLM Settings")

		self.localLLMList = QTableWidget(0, 4)
		self.localLLMList.setHorizontalHeaderLabels(["Name", "Type", "IP", "Port"])
		self.localLLMList.setFixedWidth(500)

		self.loadLocalLLMList(initSettings)

		#buttons
		buttonLayout = QHBoxLayout()
		addButton = QPushButton("Add")
		addButton.clicked.connect(self.addToLocalLLMList)
		removeButton = QPushButton("Remove")
		removeButton.clicked.connect(self.removeFromLocalLLMList)
		buttonLayout.addWidget(addButton)
		buttonLayout.addWidget(removeButton)

		#titles
		titleLayout = QHBoxLayout()
		a = QLabel("Model name")
		a.setFixedWidth(200)
		b = QLabel("Model type")
		b.setFixedWidth(100)
		c = QLabel("IP address")
		c.setFixedWidth(100)
		d = QLabel("Port")
		d.setFixedWidth(50)
		titleLayout.addWidget(a)
		titleLayout.addWidget(b)
		titleLayout.addWidget(c)
		titleLayout.addWidget(d)

		# #name
		LLMSettingLayout = QHBoxLayout()

		self.LLMName = QLineEdit()
		self.LLMName.setFixedWidth(200)
		LLMSettingLayout.addWidget(self.LLMName)

		self.typeCombo = QComboBox()
		self.typeCombo.addItem("LM Studio")
		self.typeCombo.setFixedWidth(100)
		LLMSettingLayout.addWidget(self.typeCombo)

		self.IPAddress = QLineEdit()
		self.IPAddress.setFixedWidth(100)
		LLMSettingLayout.addWidget(self.IPAddress)

		self.port = QLineEdit()
		self.port.setFixedWidth(50)
		LLMSettingLayout.addWidget(self.port)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("Local LLMs"))
		layout.addWidget(self.localLLMList)
		layout.addLayout(titleLayout)
		layout.addLayout(LLMSettingLayout)
		layout.addLayout(buttonLayout)
		self.setLayout(layout)
	
	def loadLocalLLMList(self, initSettings):
		rowCt = 0
		for modelName in initSettings:
			type = initSettings[modelName]["type"]
			ip = initSettings[modelName]["IP"]
			port = initSettings[modelName]["port"]
			self.localLLMList.insertRow(rowCt)
			modelName = QTableWidgetItem(modelName)
			type = QTableWidgetItem(type)
			ip = QTableWidgetItem(ip)
			port = QTableWidgetItem(str(port))
			modelName.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
			type.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
			ip.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
			port.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
			self.localLLMList.setItem(rowCt, 0, modelName)
			self.localLLMList.setItem(rowCt, 1, type)
			self.localLLMList.setItem(rowCt, 2, ip)
			self.localLLMList.setItem(rowCt, 3, port)
			rowCt += 1

	def addToLocalLLMList(self):
		rowCount = self.localLLMList.rowCount()

		if len(self.LLMName.text().strip()) == 0 or self.LLMName.text().lower() == "gpt" or self.LLMName.text().lower() == "gemini":
			return
	
		if len(self.IPAddress.text().strip()) == 0:
			return

		if len(self.port.text().strip()) == 0:
			return	
		
		try:
			x = int(self.port.text())
			if x < 0 or x > 65535:
				return
		except ValueError as e:
			print("Default value must be a valid port number")
			return
		
		for i in range(rowCount):
			if self.LLMName.text().strip() == self.localLLMList.item(i, 0).text():
				return
			if self.IPAddress.text().strip() == self.localLLMList.item(i, 2).text() and int(self.port.text().strip()) == int(self.localLLMList.item(i, 3).text()):
				return
		
		if not self.LLMName.text().isidentifier():
			print("Must be a valid variable name")
			return
		
		v = QTableWidgetItem(self.LLMName.text())
		w = QTableWidgetItem(self.typeCombo.currentText()) 
		x = QTableWidgetItem(self.IPAddress.text())  
		y = QTableWidgetItem(self.port.text())          

		v.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
		w.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
		x.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 
		y.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled) 

		self.localLLMList.insertRow(rowCount)
		self.localLLMList.setItem(rowCount, 0, v) 
		self.localLLMList.setItem(rowCount, 1, w) 
		self.localLLMList.setItem(rowCount, 2, x)
		self.localLLMList.setItem(rowCount, 3, y)
	

	def removeFromLocalLLMList(self):
		curRow = self.localLLMList.currentRow()
		if self.localLLMList.item(curRow, 0) == None:
			return
		modelName = self.localLLMList.item(curRow, 0).text()
		if self.parentScene.doesScriptUseLocalModel(modelName):
			dlg = QMessageBox()
			dlg.setWindowTitle("Delete local model?")
			dlg.setText("This model is being used and will be removed from the script. Are you sure you want to delete it?")
			dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			ret = dlg.exec()
			if ret == QMessageBox.Yes:
				self.localLLMList.removeRow(curRow)
		else:
			self.localLLMList.removeRow(curRow)
	
		