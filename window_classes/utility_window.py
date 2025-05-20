from PyQt5.QtWidgets import QDialogButtonBox, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QComboBox, QSpinBox, QPushButton, QListView, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class WaitWindow(QDialog):
	def __init__(self, initWait):
		super().__init__()
		
		self.setWindowTitle("Wait")
		layout = QVBoxLayout()

		self.waitTime = QSpinBox()
		self.waitTime.setFixedWidth(100)
		self.waitTime.setMinimum(0)
		self.waitTime.setMaximum(100000)
		self.waitTime.setSingleStep(200)
		self.waitTime.setValue(initWait)

		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Time to wait (ms)"))
		layout.addWidget(self.waitTime)
		layout.addWidget(buttons)
		self.setLayout(layout)

class TimerWindow(QDialog):
	def __init__(self, initTimer):
		super().__init__()
		
		self.setWindowTitle("Timer")
		layout = QVBoxLayout()

		self.timerTime = QSpinBox()
		self.timerTime.setFixedWidth(100)
		self.timerTime.setMinimum(1)
		self.timerTime.setMaximum(100000)
		self.timerTime.setSingleStep(1)
		self.timerTime.setValue(initTimer)

		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Set timer to elapse (seconds)"))
		layout.addWidget(self.timerTime)
		layout.addWidget(buttons)
		self.setLayout(layout)

class RandomDecisionWindow(QDialog):

	# update function is start or stop
	def __init__(self, initNum):
		super().__init__()

		self.setWindowTitle("Random decision")
		layout = QVBoxLayout()

		self.numDecisions = QSpinBox()
		self.numDecisions.setFixedWidth(100)
		self.numDecisions.setMinimum(1)
		self.numDecisions.setMaximum(20)
		self.numDecisions.setSingleStep(1)
		self.numDecisions.setValue(initNum)

		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("How many paths to randomize?"))
		layout.addWidget(self.numDecisions)
		layout.addWidget(buttons)

		self.setLayout(layout)

class TTSParameterWindow(QDialog):
	def __init__(self, initParams):
		super().__init__()

		self.params = []
		
		self.setWindowTitle("TTS Parameters")
		layout = QVBoxLayout()

		paramLayout = QHBoxLayout()
		self.parameterChanges = QListView()
		self.itemModel = QStandardItemModel()
		self.parameterChanges.setModel(self.itemModel)
		for p in initParams:
			row = QStandardItem(p[0] + "\t" + str(p[1]))
			self.itemModel.appendRow(row)
			self.params.append(p)
		self.removeButton = QPushButton("Remove")
		self.removeButton.clicked.connect(self.removeUpdate)

		paramLayout.addWidget(self.parameterChanges)
		paramLayout.addWidget(self.removeButton)

		valueLayout = QHBoxLayout()
		self.paramCombo = QComboBox()
		self.paramCombo.addItems(["Speed", "Volume"])

		self.paramSpin = QSpinBox()
		self.paramSpin.setFixedWidth(100)
		self.paramSpin.setMinimum(50)
		self.paramSpin.setMaximum(200)
		self.paramSpin.setSingleStep(5)
		self.paramSpin.setValue(100)
		self.addButton = QPushButton("Add")
		self.addButton.clicked.connect(self.addParameterUpdate)

		valueLayout.addWidget(self.paramCombo)
		valueLayout.addWidget(self.paramSpin)
		valueLayout.addWidget(self.addButton)

		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addLayout(paramLayout)
		layout.addWidget(QLabel("Set TTS parameter (100 is default)"))
		layout.addLayout(valueLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)	

	def addParameterUpdate(self):		
		self.params.append([self.paramCombo.currentText(), self.paramSpin.value()])
		self.refreshList()
	
	def removeUpdate(self):
		ind = self.parameterChanges.selectedIndexes()[0].row()
		self.params.remove(self.params[ind])
		self.refreshList()

	
	def refreshList(self):
		self.itemModel.clear()
		for x in self.params:
			displayString = x[0] + "\t" + str(x[1])
			row = QStandardItem(displayString)
			self.itemModel.appendRow(row)
		self.removeButton.setEnabled(len(self.params) > 0)

	
class PythonFunctionWindow(QDialog):
	def __init__(self, scriptList, variableList, initFuncName, initVariable):
		super().__init__()

		self.setWindowTitle("Run Python Module")
		layout = QVBoxLayout()

		self.scriptCombo = QComboBox()
		self.scriptCombo.addItems(scriptList)

		if len(initFuncName) > 0:
			self.scriptCombo.setCurrentText(initFuncName)

		variableLayout = QHBoxLayout()
		variableList = [x[0] for x in variableList]
		self.variableCheck = QCheckBox()
		self.variableCheck.stateChanged.connect(self.variableCheckChanged)
		self.variableCombo = QComboBox()
		self.variableCombo.addItems(variableList)

		variableLayout.addWidget(QLabel("Save the return value into a variable?"))
		variableLayout.addWidget(self.variableCheck)
		variableLayout.addWidget(self.variableCombo)

		self.variableCheck.setChecked(len(initVariable) > 0)
		self.variableCheckChanged()

		if len(initVariable) > 0:
			self.variableCombo.setCurrentText(initVariable)
		
		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			Qt.Horizontal)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)

		layout.addWidget(QLabel("Select the Python module to call.\nModules must contain just one run() method with one script_loader as an argument.\nModules can return one value to be put into a script variable"))
		layout.addWidget(self.scriptCombo)
		layout.addLayout(variableLayout)
		layout.addWidget(buttons)
		self.setLayout(layout)
	
	def variableCheckChanged(self):
		self.variableCombo.setEnabled(self.variableCheck.isChecked())