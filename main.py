import sys
import pathlib
import script_processor
import threading
from script_server import Server
from llm.LLM_client import Client, CustomLLMClient
from PyQt5 import QtCore
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap, QPainter, QIcon, QKeySequence
from PyQt5.QtWidgets import (
	 QWidget,
	 QApplication,
	 QToolButton,
	 QMainWindow,
	 QStatusBar,
	 QToolBar,
	 QGraphicsView,
	 QFileDialog,
	 QSizePolicy,
	 QMessageBox,
	 QShortcut,
	 QVBoxLayout,
	 QTabWidget,
	 QLabel,
	 QStatusBar,
	 QMenu,
	 QAction,
	 QActionGroup)
from nodes.basic_nodes import Icon, DialogNode
from nodes.llm_nodes import RobotLLMNode, LLMDecisionNode, LLMVariableUpdateNode
from clipboard import ClipBoard
import json
import threading
import window_classes.environment_window as env_window
import window_classes.variable_window as var_window
import window_classes.word_list_window as word_list_window
import window_classes.subsequences_window as subsequences_window
import window_classes.monitoring_window as monitoring_window
import window_classes.llm_list_window as llm_list_window
import window_classes.local_llm_window as local_llm_window
import script_loader
from scene import Scene
from llm.LLM_API_server import check_for_GPT, check_for_Gemini, check_for_LMStudio
import ctypes

if sys.platform == "win32":
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScriptBoard")

class ScriptMainWindow(QMainWindow):

	monitoringUpdate = QtCore.pyqtSignal()
	monitoringClose = QtCore.pyqtSignal()
	centeringUpdate = QtCore.pyqtSignal(int, float)


	def __init__(self):
		super(ScriptMainWindow, self).__init__()

		self.name = "Main"
		self.showAdvancedNodes = False
		self.advancedNodeList = ["record", "record_off", "parameters", "behavior_start", "behavior_stop", "python_function"]
		self.monitoringUpdate.connect(self.updateMonitoringWindow)
		self.monitoringClose.connect(self.closeMonitoringWindow)
		self.centeringUpdate.connect(self.centerNode)
		self.local_llm_setting = {}
		self.custom_llm_clients = {}
		self.setServers()
		self.setCanvas()
		self.makeToolBar()
		self.makeStatusBar()
		self.initializeVariables()
		self.setSubWindows()
		self.openInitialScript()
		self.setWindowIcon(QIcon('pics/favicon.ico'))
	
	def initializeVariables(self):
		self.idctr = 0
		self.variables = []
		self.environment = []
		self.subsequences = []
		
	def setSubWindows(self):
		self.tabbedWindow = TabbedWindow()
		self.tabbedWindow.addMainTab(self.view)
		self.setCentralWidget(self.tabbedWindow)
		self.subwindows = []
	
	def setCanvas(self):
		self.scene = Scene(self)
		self.view = MyView(self.scene)
		self.view.setInteractive(True)
		self.view.setDragMode(2)
		self.view.setRenderHint(QPainter.Antialiasing)
		self.setCentralWidget(self.view)

		self.view.setAcceptDrops(True)
		self.setAcceptDrops(True)

	def openLLMChoiceRobotTalkMenu(self, position):
		menu = QMenu()

		action_group = QActionGroup(self)
		action_group.setExclusive(True)

		options = ["ChatGPT", "Gemini", "LM Studio", "Custom"]
		for option in options:
			action = QAction(option, self, checkable=True)
			action.triggered.connect(lambda checked, opt=option: self.updateLLMType(opt, "talk"))
			action_group.addAction(action)
			menu.addAction(action)		
		menu.exec_(self.robot_llm_icon.mapToGlobal(position))
	
	def openLLMChoiceDecisionMenu(self, position):
		menu = QMenu()

		action_group = QActionGroup(self)
		action_group.setExclusive(True)

		options = ["ChatGPT", "Gemini", "LM Studio", "Custom"]
		for option in options:
			action = QAction(option, self, checkable=True)
			action.triggered.connect(lambda checked, opt=option: self.updateLLMType(opt, "decision"))
			action_group.addAction(action)
			menu.addAction(action)		
		menu.exec_(self.llm_decision_icon.mapToGlobal(position))
	

	def openLLMChoiceVariableMenu(self, position):
		menu = QMenu()

		action_group = QActionGroup(self)
		action_group.setExclusive(True)

		options = ["ChatGPT", "Gemini", "LM Studio", "Custom"]
		for option in options:
			action = QAction(option, self, checkable=True)
			action.triggered.connect(lambda checked, opt=option: self.updateLLMType(opt, "variable"))
			action_group.addAction(action)
			menu.addAction(action)		
		menu.exec_(self.llm_variable_icon.mapToGlobal(position))
	

	def updateLLMType(self, llm, nodeType):

		if llm =="ChatGPT":
			if nodeType == "talk":
				pixmap= QPixmap('pics/robot_gpt.png')
				icon_type = "robot_gpt"
				tooltip = "Robot GPT node"
			elif nodeType == "decision":
				pixmap= QPixmap('pics/gpt_decision.png')
				icon_type = "gpt_decision"	
				tooltip = "GPT decision node"
			elif nodeType == "variable":
				pixmap= QPixmap('pics/gpt_variable.png')
				icon_type = "gpt_variable"
				tooltip = "GPT variable node"				

		elif llm == "Gemini":
			if nodeType == "talk":
				pixmap= QPixmap('pics/robot_gemini.png')
				icon_type = "robot_gemini"
				tooltip = "Robot Gemini node"
			elif nodeType == "decision":
				pixmap= QPixmap('pics/gemini_decision.png')
				icon_type = "gemini_decision"
				tooltip = "Gemini decision node"	
			elif nodeType == "variable":
				pixmap= QPixmap('pics/gemini_variable.png')
				icon_type = "gemini_variable"	
				tooltip = "Gemini variable node"
		
		elif llm == "LM Studio":
			if nodeType == "talk":
				pixmap= QPixmap('pics/robot_lmstudio.png')
				icon_type = "robot_lmstudio"
				tooltip = "Robot LM Studio node"
			elif nodeType == "decision":
				pixmap= QPixmap('pics/lmstudio_decision.png')
				icon_type = "lmstudio_decision"
				tooltip = "LM studio decision node"	
			elif nodeType == "variable":
				pixmap= QPixmap('pics/lmstudio_variable.png')
				icon_type = "lmstudio_variable"	
				tooltip = "LM Studio variable node"
		
		elif llm == "Custom":
			if nodeType == "talk":
				pixmap= QPixmap('pics/robot_custom.png')
				icon_type = "robot_custom"
				tooltip = "Robot Custom node"
			elif nodeType == "decision":
				pixmap= QPixmap('pics/custom_decision.png')
				icon_type = "custom_decision"
				tooltip = "Custom decision node"	
			elif nodeType == "variable":
				pixmap= QPixmap('pics/custom_variable.png')
				icon_type = "custom_variable"	
				tooltip = "Custom variable node"

		if nodeType == "talk":
			self.robot_llm_icon.set_pic(pixmap)
			self.robot_llm_icon.set_type(icon_type)
			self.robot_llm_icon.setToolTip(tooltip)
		elif nodeType == "decision":
			self.llm_decision_icon.set_pic(pixmap)
			self.llm_decision_icon.set_type(icon_type)
			self.llm_decision_icon.setToolTip(tooltip)
		elif nodeType == "variable":
			self.llm_variable_icon.set_pic(pixmap)
			self.llm_variable_icon.set_type(icon_type)	
			self.llm_variable_icon.setToolTip(tooltip)		
	
	def disableAdvancedIcons(self):
		for icon in self.topToolbar.findChildren(QLabel):
			if icon.icon_type in self.advancedNodeList:
				icon.setEnabled(False)
		
		for icon in self.bottomToolbar.findChildren(QLabel):
			if icon.icon_type in self.advancedNodeList:
				icon.setEnabled(False)

	def makeToolBar(self):
		self.setWindowTitle("ScriptBoard")

		self.topToolbar = QToolBar("Top Toolbar")
		self.topToolbar.setStyleSheet("QToolBar{spacing:15px;padding:5px;}")
		self.topToolbar.setIconSize(QSize(64,64))

		self.bottomToolbar = QToolBar("Bottom Toolbar")
		self.bottomToolbar.setStyleSheet("QToolBar{spacing:15px;padding:5px;}")
		self.bottomToolbar.setIconSize(QSize(64,64))

		self.addButton('pics/new.png', "New script", self.topToolbar,self.newScript)
		self.addButton('pics/open.png', "Open script", self.topToolbar, self.loadScriptFromFileDialog)
		self.addButton('pics/save.png', "Save script", self.topToolbar, self.saveScript)
		self.addButton('pics/save_as.png', "Save script as new file", self.topToolbar, self.saveAsScript)

		self.shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
		self.shortcut.activated.connect(self.saveScript)

		spacer = QWidget()
		spacer.setFixedWidth(150)
		spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
		self.topToolbar.addWidget(spacer)

		self.play_button = QToolButton(self)
		self.play_button.setIcon(QIcon('pics/play.png'))
		self.play_button.clicked.connect(lambda: self.playButtonClicked())
		self.topToolbar.addWidget(self.play_button)

		self.stop_button = QToolButton(self)
		self.stop_button.setIcon(QIcon('pics/stop.png'))
		self.stop_button.clicked.connect(lambda: self.stopButtonClicked())
		self.stop_button.setEnabled(False)
		self.topToolbar.addWidget(self.stop_button)

		spacer = QWidget()
		spacer.setFixedWidth(160)
		spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
		self.topToolbar.addWidget(spacer)

		self.addDraggableIcon('pics/start.png', 'start', "Start node", self.topToolbar)
		self.addDraggableIcon('pics/human.png', 'human', "Human turn node", self.topToolbar)
		self.addDraggableIcon('pics/human_target.png', 'human_target', "Human target node", self.topToolbar)
		self.addDraggableIcon('pics/robot.png', 'robot', "Robot turn node", self.topToolbar)

		self.robot_llm_icon = Icon(pixmap=QPixmap('pics/robot_gpt.png'))
		self.robot_llm_icon.set_type("robot_gpt")
		self.robot_llm_icon.setToolTip("Robot GPT node")
		self.robot_llm_icon.setContextMenuPolicy(Qt.CustomContextMenu)
		self.robot_llm_icon.customContextMenuRequested.connect(self.openLLMChoiceRobotTalkMenu)
		self.topToolbar.addWidget(self.robot_llm_icon)

		self.addDraggableIcon('pics/tts_parameters.png', 'tts_parameters', "Set TTS parameters", self.topToolbar)

		spacer = QWidget()
		spacer.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
		self.topToolbar.addWidget(spacer)

		self.addDraggableIcon('pics/wait.png', 'wait', "Wait node", self.topToolbar)
		self.addDraggableIcon('pics/timer.png', 'timer', "Timer node", self.topToolbar)
		self.addDraggableIcon('pics/variable_update.png', 'variable_update', "Variable update node", self.bottomToolbar)
	
		self.llm_variable_icon = Icon(pixmap=QPixmap('pics/gpt_variable.png'))
		self.llm_variable_icon.set_type("gpt_variable")
		self.llm_variable_icon.setToolTip("GPT variable node")
		self.llm_variable_icon.setContextMenuPolicy(Qt.CustomContextMenu)
		self.llm_variable_icon.customContextMenuRequested.connect(self.openLLMChoiceVariableMenu)
		self.bottomToolbar.addWidget(self.llm_variable_icon)

		self.addDraggableIcon('pics/reset_variables.png', 'reset_variables', "Reset variables node", self.bottomToolbar)
		self.addDraggableIcon('pics/variable_decision.png', 'variable_decision', "Variable decision node", self.bottomToolbar)

		self.llm_decision_icon = Icon(pixmap=QPixmap('pics/gpt_decision.png'))
		self.llm_decision_icon.set_type("gpt_decision")
		self.llm_decision_icon.setToolTip("GPT decision node")
		self.llm_decision_icon.setContextMenuPolicy(Qt.CustomContextMenu)
		self.llm_decision_icon.customContextMenuRequested.connect(self.openLLMChoiceDecisionMenu)
		self.bottomToolbar.addWidget(self.llm_decision_icon)

		self.addDraggableIcon('pics/random_decision.png', 'random_decision', "Random decision node", self.bottomToolbar)
		self.addDraggableIcon('pics/turn_based_decision.png', 'turn_based_decision', "Turn-based decision node", self.bottomToolbar)
		self.addDraggableIcon('pics/enter_subseq.png', 'enter_subseq', "Enter subsequence node", self.bottomToolbar)


		spacer = QWidget()
		spacer.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
		self.bottomToolbar.addWidget(spacer)

		self.addButton('pics/environment.png', "Set up environment", self.bottomToolbar, self.setEnvironment)
		self.addButton('pics/variables.png', "Variable list", self.bottomToolbar, self.setVariables)	
		self.addButton('pics/word_list.png', "Word lists", self.bottomToolbar, self.setWordLists)	
		self.addButton('pics/subsequences.png', "Subsequences", self.bottomToolbar, self.setSubsequences)
		self.addButton('pics/llms.png', "LLM selection", self.bottomToolbar, self.showLLMs)
		self.addButton('pics/local_llm.png', "Local LLM settings", self.bottomToolbar, self.showLocalLLMs)

		spacer = QWidget()
		spacer.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
		self.bottomToolbar.addWidget(spacer)

		self.addDraggableIcon('pics/python_function.png', 'python_function', "Run external Python module", self.bottomToolbar)
		self.addDraggableIcon('pics/send_to_dm.png', 'send_to_dm', "Send message to dialogue manager", self.bottomToolbar)

		self.addToolBar(self.topToolbar)
		self.addToolBarBreak()
		self.addToolBar(self.bottomToolbar)

		self.setStatusBar(QStatusBar(self))
		self.scriptRunning = False
	
	def addDraggableIcon(self, icon_filename, icon_type, tooltip, toolbar):
		icon = Icon(pixmap=QPixmap(icon_filename))
		icon.set_type(icon_type)
		icon.setToolTip(tooltip)
		toolbar.addWidget(icon)
	
	def addButton(self, icon_filename, tooltip, toolbar, click_command):
		button = QToolButton(self)
		button.setIcon(QIcon(icon_filename))
		button.clicked.connect(click_command)
		button.setToolTip(tooltip)
		toolbar.addWidget(button)


	
	def makeStatusBar(self):
		self.connectionStatusText = QLabel("")
		self.statusBar().addPermanentWidget(self.connectionStatusText)
		self.updateServerConnectionStatus(self.server.connected)

	def openInitialScript(self):
		try:
			f = open("init.ini", "r")
			for x in f.readlines():
				if x.startswith("openfile="):
					y = x.split("=")[1].strip()
					if y == "None":
						self.filename = None
					else:
						self.filename = y
						self.loadScript()
				if x.startswith("latest_node"):
					self.scene.latestClickedNodeID = int(x.split("=")[1].strip())
					if self.scene.latestClickedNodeID > 0:
						self.centerNode(self.scene.latestClickedNodeID, 0.15)
		except FileNotFoundError as e:
			self.filename = None

	def setServers(self):
		self.server = server
		self.server.set_main_window(self)
		self.llm_client = llm_client

	def updateServerConnectionStatus(self, b):
		try:
			if b == True:
				self.connectionStatusText.setText("<font color='green'>Connected to dialogue manager</font>")
			else:
				self.connectionStatusText.setText("<font color='red'>Not connected to dialogue manager</font>")
		except AttributeError as e:
			pass

	def playButtonClicked(self):
		global sourceWindowForPlay
		currentWindowName = self.tabbedWindow.getCurrentTabName()
		if currentWindowName == "Main":
			sourceWindowForPlay = self
			playScript(self)
		else:
			for s in self.subwindows:
				if s.name == currentWindowName:
					sourceWindowForPlay = s
					playScript(s)
					break
	
	def playFromRightClick(self, n):
		global sourceWindowForPlay
		sourceWindowForPlay = self
		playScript(self, nodeID=n)

	
	def stopButtonClicked(self):
		global sourceWindowForPlay
		[icon.setEnabled(True) for icon in self.topToolbar.findChildren(QWidget)]
		[icon.setEnabled(True) for icon in self.bottomToolbar.findChildren(QWidget)]
		self.stop_button.setEnabled(False)
		self.server.send_message("SCRIPT_GUI:Stopped")
		sourceWindowForPlay.scriptRunning = False
		sourceWindowForPlay.closeMonitoringWindow()
		sourceWindowForPlay = None
		currentWindowName = self.tabbedWindow.getCurrentTabName()

		if currentWindowName == "Main":
			self.view.scale(0.5, 0.5)
		else:
			for s in self.subwindows:
				if s.name == currentWindowName:
					s.view.scale(0.5, 0.5)
		
		self.scene.enableAllNodes()
		for window in self.subwindows:
			window.scene.enableAllNodes()


	def closeMonitoringWindow(self):
		if self.processor != None:
			self.processor.close_monitoring_window()
		
	def disableIconsWhilePlaying(self):

		for button in self.topToolbar.findChildren(QToolButton):
			if button != self.stop_button:
				button.setEnabled(False)
		
		for button in self.bottomToolbar.findChildren(QToolButton):
			if button != self.stop_button:
				button.setEnabled(False)
		
		[icon.setEnabled(False)for icon in self.topToolbar.findChildren(QLabel)]
		[icon.setEnabled(False)for icon in self.bottomToolbar.findChildren(QLabel)]

		self.scene.disableAllNodes()
		for window in self.subwindows:
			window.scene.disableAllNodes()
	


	def stopScript(self):
		[icon.setEnabled(True) for icon in self.topToolbar.findChildren(QWidget)]
		[icon.setEnabled(True) for icon in self.bottomToolbar.findChildren(QWidget)]
		self.stop_button.setEnabled(False)
		self.server.send_message("SCRIPT_GUI:Stopped")
		self.scriptRunning = False
		self.view.scale(0.5, 0.5)
		self.scene.enableAllNodes()
		for window in self.subwindows:
			window.scene.enableAllNodes()

	def setVariables(self):
		dlg = var_window.VariableWindow(self)
		dlg.exec()
		self.variables = dlg.getVariableList()

	def setEnvironment(self):
		dlg = env_window.EnvironmentWindow(self.environment, self)
		dlg.exec()
		self.environment = dlg.getHumanData()
	
	def setWordLists(self):
		dlg = word_list_window.WordListWindow(self)
		dlg.exec()
	
	def setSubsequences(self):
		prev = self.subsequences
		dlg = subsequences_window.SubsequencesWindow(self.subsequences)
		accept = dlg.exec()
		if accept == 1:
			self.subsequences = dlg.subsequences
		newSubseq = [x for x in self.subsequences if x not in prev]
		removedSubSeq = [x for x in prev if x not in self.subsequences]
		
		for x in newSubseq:
			self.addSubSequenceWindow(x)
		
		for x in removedSubSeq:
			self.removeSubSequenceWindow(x)
	
	def showLLMs(self):
		dlg = llm_list_window.LLMListWindow(self.local_llm_setting, self.custom_llm_clients)
		dlg.exec()
	
	def showLocalLLMs(self):
		dlg = local_llm_window.LocalLLMWindow(self.local_llm_setting, self.scene)
		dlg.exec()
		localLLMList = dlg.localLLMList
		modelnum = localLLMList.rowCount()
		self.local_llm_setting = {}
		for i in range(modelnum):
			modelName = localLLMList.item(i, 0).text()
			modelType = localLLMList.item(i, 1).text()
			modelIP = localLLMList.item(i, 2).text()
			modelPort = int(localLLMList.item(i, 3).text())
			settings = {"type": modelType, "IP": modelIP, "port": modelPort}
			self.local_llm_setting[modelName] = settings
			if modelType == "Custom":
				# check if there are any new clients
				if modelName not in self.custom_llm_clients:
					self.add_custom_LLM_client(modelName, modelIP, modelPort)
		# remove any old clients
		clients_to_remove = []
		for c in self.custom_llm_clients:
			if c not in self.local_llm_setting:
				self.custom_llm_clients[c].shutdown()
				clients_to_remove.append(c)
		for model in clients_to_remove:
			del self.custom_llm_clients[model]

		self.scene.setSceneChanged(True)
	
	def add_custom_LLM_client(self, name, ip, port):
		# create a new custom LLM client
		custom_client = CustomLLMClient(ip, port)
		t = threading.Thread(target=custom_client.start_connecting, args=())
		t.daemon = True
		t.start()
		self.custom_llm_clients[name] = custom_client


	def addSubSequenceWindow(self, name):
		subwindow = ScriptSubWindow(name)
		subwindow.idctr = self.idctr
		subwindow.setMainWindow(self)
		subwindow.resize(1200, 1000)
		subwindow.variables = self.variables
		subwindow.environment = self.environment
		subwindow.filename = self.filename
		subwindow.subsequences = self.subsequences
		subwindow.play_button = self.play_button
		subwindow.stop_button = self.stop_button
		subwindow.topToolbar = self.topToolbar
		subwindow.bottomToolbar = self.bottomToolbar
		self.tabbedWindow.addSubsequenceTab(subwindow.view, name)
		self.subwindows.append(subwindow)
	
	def removeSubSequenceWindow(self, name):
		subwindow = self.getSubSequenceWindow(name)
		self.subwindows.remove(subwindow)
		self.tabbedWindow.removeSubsequenceTab(name)
	
	def getSubSequenceWindow(self, name):
		for x in self.subwindows:
			if x.name == name:
				return x

		return None

	def updateVariableName(self, oldName, newName):
		for x in self.variables:
			if x[0] == oldName:
				x[0] = newName
				self.scene.updateVariableNameForScript(oldName, newName)
				break
	
	def newScript(self):
		dlg = QMessageBox()
		dlg.setWindowTitle("Save changes?")
		dlg.setText("Do you want to save your changes?")
		dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		ret = dlg.exec()
		if ret == QMessageBox.Yes:
			self.saveScript()

		#remove any subwindows
		removedSubSeq = [s.name for s in self.subwindows]
		for name in removedSubSeq:
			self.removeSubSequenceWindow(name)
		self.scene.clear()
		self.idctr = 0
		self.variables = []
		self.environment = []
		self.subsequences = []
		self.local_llm_setting = {}
		self.custom_llm_clients = {}
		self.filename = None
		self.setWindowTitle("ScriptBoard")
		self.scene.setSceneChanged(False)


		
	def saveScript(self):
		if self.filename == None:
			fileName, _ = QFileDialog.getSaveFileName(self,"Save script","","Script Files(*.json)")
			if len(fileName) > 0:
				self.filename = fileName
			else:
				return

		self.createJSON()
		self.setWindowTitle("ScriptBoard (" + self.filename + ")")
		print("File saved")
		self.scene.setSceneChanged(False)
	
	def saveAsScript(self):
		fileName, _ = QFileDialog.getSaveFileName(self,"Save script","","Script Files(*.json)")
		if len(fileName) > 0:
			self.filename = fileName
		else:
			return
		self.createJSON()
		self.setWindowTitle("ScriptBoard (" + self.filename + ")")
		print("File saved")
		self.scene.setSceneChanged(False)
	
	def createJSON(self):

		nodes = self.getNodeDictionary()

		#for subsequences
		for ind, window in enumerate(self.subwindows):
			subseqDict = {}
			subseqNodes = window.getNodeDictionary()
			subseqDict["nodes"] = subseqNodes
			subseqDict["name"] = window.name
			nodes["Subsequence" + str(ind)] = subseqDict

		with open(self.filename, 'w', encoding="utf-8") as f:
			json.dump(nodes, f, ensure_ascii=False, indent=4)
	
	def getNodeDictionary(self):

		nodes = {}
		ct = 0
		for item in self.scene.items():
			if isinstance(item, DialogNode):
				infoDict = item.retrieveInfo()
				connectors = []
				for conn in item.connectors:
					connInfo = conn.retrieveInfo()
					connectors.append(connInfo)
				infoDict["connectors"] = connectors
				nodes["Node" + str(ct)] = infoDict
				ct +=1
		
		varCt = 0
		for x in self.variables:
			y = {}
			y["name"] = x[0]
			y['type'] = x[1]
			y['value'] = x[2]
			nodes["Variable" + str(varCt)] = y
			varCt += 1
		
		environment = {}
		humCt = 0
		for x in self.environment:
			y = {}
			y["human ID"] = x[0]
			y["target"] = x[1]
			environment["Human" + str(humCt)] = y
			humCt += 1
		nodes["Environment"] = environment
		nodes["Local LLMs"] = self.local_llm_setting
		return nodes

	#call can come from other scene so need to check everything
	def getOwnerOfJoint(self, joint):

		#first check main window
		for n in self.scene.items():
			if isinstance(n, DialogNode):
				for conn in n.connectors:
					if conn == joint:
						return n
		
		#then check all other windows
		for w in self.subwindows:
			for n in w.scene.items():
				if isinstance(n, DialogNode):
					for conn in n.connectors:
						if conn == joint:
							return n
	
	
	def loadScriptFromFileDialog(self):
		fileName, filter = QFileDialog.getOpenFileName(self, "Load script","","Script Files(*.json)")

		if len(fileName) > 0:
			self.filename = fileName
			self.loadScript()
	
	def loadScript(self):
		#remove any subwindows
		removedSubSeq = [s.name for s in self.subwindows]
		for name in removedSubSeq:
			self.removeSubSequenceWindow(name)

		script_loader.loadScript(self, self.scene)
		self.tabbedWindow.showMainTab()
		self.setWindowTitle("ScriptBoard (" + self.filename + ")")
	
	def isScriptMultiHuman(self):
		return len(self.environment) > 1

	def zoomOut(self):
		self.view.scale(0.9, 0.9)
	
	def zoomIn(self):
		self.view.scale(1.1, 1.1)
	
	def centerNode(self, node_id, scaleValue):
		node = self.scene.getNodeGivenID(node_id)
		if node != None:
			self.view.fitInView(node, Qt.KeepAspectRatio)
			self.view.scale(scaleValue, scaleValue)

	def closeEvent(self,event):
		hasChanged = False
		if self.scene.sceneChanged:
			hasChanged = True
		
		for w in self.subwindows:
			if w.scene.sceneChanged:
				hasChanged = True
	
		if hasChanged:
			result = QMessageBox.question(self, "Confirm Exit...", "Are you sure you want to quit?\nYou will lose all unsaved changes.", QMessageBox.Yes| QMessageBox.No)
			event.ignore()

			if result == QMessageBox.Yes:
				event.accept()
				self.writeIniFile()
		else:
			event.accept()
			self.writeIniFile()
	
	def writeIniFile(self):
		f = open("init.ini", "w")
		f.write("openfile=" + str(self.filename) + "\n")
		f.write("latest_node=" + str(self.scene.latestClickedNodeID))
		f.close()
	
	def setIDCounter(self, num):
		self.idctr = num

	def incrementID(self):
		self.idctr += 1
		
	def doAllSubWindowsHaveStartNode(self):
		for s in self.subwindows:
			if s.scene.getStartNode() == None:
				return False
		return True

	def getMainWindow(self):
		return self
	
	def getAllWindows(self):
		return [self] + [s for s in self.subwindows]

	def showWindow(self, windowName=""):
		if len(windowName) == 0:
			self.tabbedWindow.showMainTab()
		else:
			self.tabbedWindow.showTab(windowName)
	
	def getCenterOfScene(self):
		return self.view.mapToScene(self.view.viewport().rect().center())

	def getMousePosition(self, mousePos):
		return self.view.mapToScene(mousePos)
	
	def createMonitoringWindow(self, variable_dict):
		self.monitoring_window = monitoring_window.MonitoringWindow(variable_dict)
		self.monitoring_window.move(0, 100)
		self.monitoring_window.show()
	
	def doUpdate(self):
		self.monitoringUpdate.emit()
	
	def doUpdateCloseMonitoringWindow(self):
		self.monitoringClose.emit()
		
	def updateMonitoringWindow(self):
		self.monitoring_window.updateStatus(self.processor.dialog_history, self.processor.variable_dict)

	def closeMonitoringWindow(self):
		self.monitoring_window.close()
	
	def doCentering(self, node_id, scale):
		self.centeringUpdate.emit(node_id, scale)

	def pasteNode(self, x, y):
		self.scene.pasteNode(mouseX=x, mouseY=y)
	
	def setCopiedNodes(self, nodes, source):
		clipboard.copiedNodes = nodes
		clipboard.copiedSource = source
	
	def getCopiedNodes(self):
		return clipboard.copiedNodes

	def getCopiedSource(self):
		return clipboard.copiedSource

	def addActionToClipboard(self, action):
		clipboard.latestActions.append(action)
	
	def undoLatestAction(self, scene):
		clipboard.undoAction(scene)
	
	def getLocalLLMSetting(self):
		return self.local_llm_setting


class ScriptSubWindow(ScriptMainWindow):
	def __init__(self, name):
		super(ScriptSubWindow, self).__init__()
		self.mainWindow = None
		self.name = name

	def setCanvas(self):
		return super().setCanvas()
	
	def makeToolBar(self):
		pass

	def initializeVariables(self):
		return super().initializeVariables()

	def getLocalLLMSetting(self):
		return super().local_llm_setting

	def openInitialScript(self):
		pass

	def setMainWindow(self, window):
		self.mainWindow = window
	
	def getMainWindow(self):
		return self.mainWindow
	
	def getAllWindows(self):
		return self.getMainWindow().getAllWindows()
	
	#have to pass this back to the main window so it does the incrementing
	def incrementID(self):
		self.mainWindow.incrementID()
	
	def saveScript(self):
		self.mainWindow.saveScript()
	
	def getSubSequenceWindow(self, name):
		return super().getSubSequenceWindow(name)
	
	def disableIconsWhilePlaying(self):
		self.mainWindow.disableIconsWhilePlaying()
	
	def getNodeDictionary(self):

		nodes = {}
		ct = 0
		for item in self.scene.items():
			if isinstance(item, DialogNode):
				infoDict = item.retrieveInfo()
				connectors = []
				for conn in item.connectors:
					connInfo = conn.retrieveInfo()
					connectors.append(connInfo)
				infoDict["connectors"] = connectors
				nodes["Node" + str(ct)] = infoDict
				ct +=1
		return nodes
	
class MyView(QGraphicsView):

	def __init__(self, scene):
		super(MyView, self).__init__(scene)
	
	def contextMenuEvent(self, event):
		context_menu = QMenu(self)

		selectedNodes = [x for x in self.scene().items() if x.isSelected() == True and isinstance(x, DialogNode)]
		if len(selectedNodes) == 1:
			if isinstance(selectedNodes[0], RobotLLMNode) or isinstance(selectedNodes[0], LLMDecisionNode) or isinstance(selectedNodes[0], LLMVariableUpdateNode):
				submenu = QMenu("Set LLM", self)
				GPTAction = QAction("GPT", self)
				GPTAction.triggered.connect(lambda: self.scene().setLLMForNode(selectedNodes[0], "gpt"))
				GeminiAction = QAction("Gemini", self)
				GeminiAction.triggered.connect(lambda: self.scene().setLLMForNode(selectedNodes[0], "gemini"))
				LMStudioAction = QAction("LM Studio", self)
				LMStudioAction.triggered.connect(lambda: self.scene().setLLMForNode(selectedNodes[0], "lmstudio"))
				customAction = QAction("Custom", self)
				customAction.triggered.connect(lambda: self.scene().setLLMForNode(selectedNodes[0], "custom"))
				submenu.addAction(GPTAction)
				submenu.addAction(GeminiAction)
				submenu.addAction(LMStudioAction)
				submenu.addAction(customAction)
				context_menu.addMenu(submenu)
			copyAction = QAction("Copy node", self)
			copyAction.triggered.connect(lambda: self.scene().copyNode(selectedNodes))
			startAction = QAction("Start script here", self)
			startAction.triggered.connect(selectedNodes[0].startNode)
			context_menu.addAction(startAction)
			context_menu.addAction(copyAction)
		elif len(selectedNodes) > 1:
			copyAction = QAction("Copy nodes", self)
			copyAction.triggered.connect(lambda: self.scene().copyNode(selectedNodes))
			context_menu.addAction(copyAction)
		else:
			# Add actions to the menu
			pasteAction = QAction('Paste Nodes', self)
			pasteAction.triggered.connect(lambda:self.scene().pasteNode(self.mapToScene(event.pos()).x(), self.mapToScene(event.pos()).y()))

			undoAction = QAction('Undo', self)
			undoAction.triggered.connect(self.scene().undoAction)
			# Add actions to the context menu
			context_menu.addAction(pasteAction)
			context_menu.addAction(undoAction)

		# Show the context menu at the position of the mouse cursor
		context_menu.exec_(event.globalPos())
		

class TabbedWindow(QWidget):

	def __init__(self):
		super(QWidget, self).__init__()
		self.layout = QVBoxLayout(self)
		# Initialize tab screen
		self.tabs = QTabWidget()

	def addMainTab(self, view):
		
		self.mainTab = QWidget()
		self.tabs.addTab(self.mainTab, "Main")
		
		self.mainTab.layout = QVBoxLayout()
		self.mainTab.layout.addWidget(view)
		self.mainTab.setLayout(self.mainTab.layout)
		
		self.layout.addWidget(self.tabs)
		self.setLayout(self.layout)
	
	def showMainTab(self):
		self.tabs.setCurrentIndex(0)
	
	def showTab(self, name):
		for i in range(self.tabs.count()):
			if self.tabs.tabText(i) == name:
				self.tabs.setCurrentIndex(i)
				break

	def addSubsequenceTab(self, view, name):
		subTab = QWidget()
		self.tabs.addTab(subTab, name)

		subTab.layout = QVBoxLayout()
		subTab.layout.addWidget(view)
		subTab.setLayout(subTab.layout)
		self.tabs.setCurrentIndex(len(self.tabs)-1)
	
	def removeSubsequenceTab(self, name):
		for i in range(self.tabs.count()):
			if self.tabs.tabText(i) == name:
				self.tabs.removeTab(i)
				print("Removed ", name)
				break
	
	def getCurrentTabName(self):
		for i in range(self.tabs.count()):
			if i == self.tabs.currentIndex():
				return self.tabs.tabText(i) 
		return None
	

def playScript(window, nodeID=None):

	if not window.server.connected:
		msgBox = QMessageBox()
		msgBox.setWindowTitle("Not connected!")
		msgBox.setText("Script is not connected to a dialogue manager!")
		msgBox.exec()
		return

	if window.filename != None:
		if nodeID == None:
			nodeID = window.scene.getStartNode()
			subWindowStart = window.doAllSubWindowsHaveStartNode()
			if nodeID == None:
				msgBox = QMessageBox()
				msgBox.setWindowTitle("No start node found!")
				msgBox.setText("Your script does not contain a start node. Either create a start node or launch the script by right clicking from a dialog node")
				msgBox.exec()
			elif subWindowStart == False:
				msgBox = QMessageBox()
				msgBox.setWindowTitle("No start node found for a subsequence!")
				msgBox.setText("One or more subsequences does not contain a start node. Create a start node.")
				msgBox.exec()
			elif len(window.environment) == 0:
				msgBox = QMessageBox()
				msgBox.setWindowTitle("No human in the script!")
				msgBox.setText("You must specify at least one human in the environment. Set up the environment by clicking on the globe icon in the top right of the toolbar.")
				msgBox.exec()
			else:
				if window.scene.sceneChanged:
					dlg = QMessageBox()
					dlg.setWindowTitle("Save changes?")
					dlg.setText("Save changes before running script?")
					dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
					ret = dlg.exec()
					if ret == QMessageBox.Yes:
						window.saveScript()
					else:
						return
				windows = window.getAllWindows()

				for w in windows:
					if w.scene.doesScriptUseLLM("gpt"):
						# check for GPT
						GPT_available = check_for_GPT()
						if GPT_available != 0:
							dlg = QMessageBox()
							dlg.setWindowTitle("Run without LLM?")
							dlg.setText("This script uses GPT but this is not currently available. Run anyway?")
							dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
							ret = dlg.exec()
							if ret == QMessageBox.Yes:
								break
							else:
								return
						break

				for w in windows:
					if w.scene.doesScriptUseLLM("gemini"):
						# check for Gemini
						Gemini_available = check_for_Gemini()
						if Gemini_available != 0:
							dlg = QMessageBox()
							dlg.setWindowTitle("Run without LLM?")
							dlg.setText("This script uses Gemini but this is not currently available. Run anyway?")
							dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
							ret = dlg.exec()
							if ret == QMessageBox.Yes:
								break
							else:
								return
						break
				
				for w in windows:
					if w.scene.doesScriptUseLLM("lmstudio"):
						localModels = w.scene.getAllUsedLocalModels()
						localModelSettings = w.getMainWindow().local_llm_setting
						if len(localModelSettings) == 0:
							dlg = QMessageBox()
							dlg.setWindowTitle("No LM Studio Models")
							dlg.setText("There are no local LLM models set in the script. Please define them by clicking on the local LLM window.")
							ret = dlg.exec()
							return
							
						# check for LM Studio local models
						LMStudio_available = 0
						for m in localModels:
							if m not in localModelSettings:
								if m == "":
									dlg = QMessageBox()
									dlg.setWindowTitle("Local LLM does not exist")
									dlg.setText("There is a local LLM node without a model name.")
									ret = dlg.exec()
								else:
									dlg = QMessageBox()
									dlg.setWindowTitle("Local LLM does not exist")
									dlg.setText("The defined local LLM model " + m +  " is used in the script but not defined in the local LLM list.")
									ret = dlg.exec()
								return
							else:
								setting = localModelSettings[m]	
								LMStudio_available = check_for_LMStudio(setting["IP"], setting["port"])							
							
						if LMStudio_available != 0:
							dlg = QMessageBox()
							dlg.setWindowTitle("Run without LLM?")
							dlg.setText("This script cannot connect to the defined LM Studio model. Run anyway?")
							dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
							ret = dlg.exec()
							if ret == QMessageBox.Yes:
								break
							else:
								return
						break
				
				# check for custom models
				for w in windows:
					if w.scene.doesScriptUseLLM("custom"):
						localModels = w.scene.getAllUsedLocalModels()
						localModelSettings = w.getMainWindow().local_llm_setting
						if len(localModelSettings) == 0:
							dlg = QMessageBox()
							dlg.setWindowTitle("No Custom Models")
							dlg.setText("There are no local LLM models set in the script. Please define them by clicking on the local LLM window.")
							ret = dlg.exec()
							return
							
						# check for LM Studio local models
						custom_available = 0
						for m in localModels:
							if m not in localModelSettings:
								if m == "":
									dlg = QMessageBox()
									dlg.setWindowTitle("Custom model does not exist")
									dlg.setText("There is a custom model node without a model name.")
									ret = dlg.exec()
								else:
									dlg = QMessageBox()
									dlg.setWindowTitle("Local LLM does not exist")
									dlg.setText("The defined custom model " + m +  " is used in the script but not defined in the local LLM list.")
									ret = dlg.exec()
								return
							else:
								setting = localModelSettings[m]
								client = window.custom_llm_clients[m]
								if not client.connected:
									custom_available = -1
							
						if custom_available != 0:
							dlg = QMessageBox()
							dlg.setWindowTitle("Run without custom model?")
							dlg.setText("This script cannot connect to the defined custom model. Run anyway?")
							dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
							ret = dlg.exec()
							if ret == QMessageBox.Yes:
								break
							else:
								return
						break

				window.processor = script_processor.ScriptProcessor(window)
				window.play_button.setEnabled(False)
				window.stop_button.setEnabled(True)
				window.scriptRunning = True
				t1 = threading.Thread(target=window.processor.start, args=(nodeID,))
				t1.daemon = True
				t1.start()
				window.server.send_message("SCRIPT_GUI:PLAY#" + pathlib.Path(window.filename).name)
				window.disableIconsWhilePlaying()

		elif len(window.environment) == 0:
			msgBox = QMessageBox()
			msgBox.setWindowTitle("No human in the script!")
			msgBox.setText("You must specify at least one human in the environment. Set up the environment by clicking on the globe icon in the top right of the toolbar.")
			msgBox.exec()
		else:
			if window.scene.sceneChanged:
				dlg = QMessageBox()
				dlg.setWindowTitle("Save changes?")
				dlg.setText("Save changes before running script?")
				dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
				ret = dlg.exec()
				if ret == QMessageBox.Yes:
					window.saveScript()
				else:
					return
			window.processor = script_processor.ScriptProcessor(window)
			window.play_button.setEnabled(False)
			window.stop_button.setEnabled(True)
			window.scriptRunning = True
			t1 = threading.Thread(target=window.processor.start, args=(nodeID,))
			t1.daemon = True
			t1.start()
			window.server.send_message("SCRIPT_GUI:" + pathlib.Path(window.filename).name)
	else:
		msgBox = QMessageBox()
		msgBox.setText("You must save your script before launching it.")
		msgBox.exec()
		window.saveScript()

server = Server(5050)

# The LLM server API client
llm_client = Client("localhost", 5042)
t2 = threading.Thread(target=llm_client.start_connecting, args=())
t2.daemon = True
t2.start()

app = QApplication(sys.argv)
app.setWindowIcon(QIcon('pics/favicon.ico'))

#main window
mainWindow = ScriptMainWindow()
mainWindow.resize(1200, 1000)
mainWindow.showMaximized()

t1 = threading.Thread(target=server.start_connecting, args=())
t1.daemon = True
t1.start()

clipboard = ClipBoard()

sourceWindowForPlay = None

app.exec()
