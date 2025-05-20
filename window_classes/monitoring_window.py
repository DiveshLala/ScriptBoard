from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QDialog, QListView, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import time


class MonitoringWindow(QDialog):
	def __init__(self, variable_dict):
		super().__init__()
		
		self.setWindowTitle("Monitor")
		self.setWindowFlag(Qt.WindowCloseButtonHint, False)
		layout = QHBoxLayout()
		
		dialogLayout = QVBoxLayout()
		self.dialogHistory = QListView()
		dialogLayout.addWidget(QLabel("Dialogue History"))
		dialogLayout.addWidget(self.dialogHistory)
		self.dialogueItemModel = QStandardItemModel()
		self.dialogHistory.setModel(self.dialogueItemModel)
		self.dialogHistory.setEditTriggers(QAbstractItemView.NoEditTriggers)

		variableLayout = QVBoxLayout()
		self.variableList = QListView()
		variableLayout.addWidget(QLabel("Variables"))
		variableLayout.addWidget(self.variableList)
		self.variableItemModel = QStandardItemModel()
		self.variableList.setModel(self.variableItemModel)
		self.variableList.setEditTriggers(QAbstractItemView.NoEditTriggers)

		self.updateStatus([], variable_dict)

		layout.addLayout(dialogLayout)
		layout.addLayout(variableLayout)
		self.setLayout(layout)
	

	def updateStatus(self, dialogueHistory, variable_dict):
		self.dialogueItemModel.clear()
		self.variableItemModel.clear()

		for d in dialogueHistory:
			c = QStandardItem(d[0] + ":" + d[1])
			self.dialogueItemModel.appendRow(c)
		
		for k in variable_dict.keys():
			c = QStandardItem(k + "= " + str(variable_dict[k][1]))
			self.variableItemModel.appendRow(c)
		
		time.sleep(0.05)
		self.dialogHistory.scrollToBottom()