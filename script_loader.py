from icons import *
import json
from condition import Condition, MultiCondition
from prompt import DialogPrompt
from PyQt5.QtGui import QPixmap


def loadScript(window,scene,jsondata=None):

	scene.clear()

	if jsondata == None: #main window
		with open(window.filename, encoding="utf-8") as f:
			data = json.load(f)
			window.variables = []
			window.environment = []
	else: #subsequences
		data = jsondata

	maxID = 0
	connectionPairs = []
	maxX = -10000000000
	minX = 10000000000
	maxY = -1000000000
	minY = 1000000000

	for i in data.keys():
		
		#variables
		if i.startswith("Variable"):
			variableData = [data[i]["name"], data[i]["type"], data[i]["value"]]
			window.variables.append(variableData)
			continue
	
		#humans
		if i == "Environment":
			for j in data[i].keys():
				human = [data[i][j]["human ID"], data[i][j]["target"]]
				window.environment.append(human)
			continue

		#subsequences
		if i.startswith("Subsequence"):
			window.subsequences.append(data[i]["name"])
			window.addSubSequenceWindow(data[i]["name"])
			subwindow = window.getSubSequenceWindow(data[i]["name"])
			loadScript(subwindow, subwindow.scene, jsondata= data[i]["nodes"])
			continue

		#nodes
		id = int(data[i]["id"])
		if id > maxID:
			maxID = id
		xpos = data[i]["xpos"]
		ypos = data[i]["ypos"]
		nodeType = data[i]["type"]

		if xpos < minX: minX = xpos
		if xpos > maxX: maxX = xpos
		if ypos < minY: minY = ypos
		if ypos > maxY: maxY = ypos

		#add nodes
		if nodeType == "robot":
			pixmap = QPixmap("pics/robot.png")
			node = RobotNode(id, pixmap.width(), pixmap.height(), scene)
			node.dialog = data[i]["dialog"]
			node.tag = data[i]["tag"]
			node.emotion = data[i]["emotion"]
			node.gesture = data[i]["gesture"]
			node.gaze = data[i]["gaze"]
			node.labelText = node.dialog.strip()[:20] + "..."
			try:
				node.bargeIn = data[i]["barge-in"]
			except KeyError as e:
				print("Barge in tag not found. Ignoring...")
		elif nodeType == "robot_gpt":
			pixmap = QPixmap("pics/robot_gpt.png")
			node = RobotGPTNode(id, pixmap.width(), pixmap.height(), scene)
			node.labelText = data[i]["label"]
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
			node.gaze = data[i]["gaze"]
			node.bargeIn = data[i]["barge-in"]
		elif nodeType == "robot_gemini":
			pixmap = QPixmap("pics/robot_gemini.png")
			node = RobotGeminiNode(id, pixmap.width(), pixmap.height(), scene)
			node.labelText = data[i]["label"]
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
			node.gaze = data[i]["gaze"]
			node.bargeIn = data[i]["barge-in"]
		elif nodeType == "robot_lmstudio":
			pixmap = QPixmap("pics/robot_lmstudio.png")
			node = RobotLMStudioNode(id, pixmap.width(), pixmap.height(), scene)
			node.labelText = data[i]["label"]
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
			node.gaze = data[i]["gaze"]
			node.bargeIn = data[i]["barge-in"]
		elif nodeType == "human":
			pixmap = QPixmap("pics/human.png")
			node = HumanNode(id, pixmap.width(), pixmap.height(), scene)
		elif nodeType == "human_target":
			pixmap = QPixmap("pics/human_target.png")
			node = HumanTargetNode(id, pixmap.width(), pixmap.height(), scene)
			node.new_target = data[i]["new target"]
			node.labelText = "Target is\n" + node.new_target
		elif nodeType == "start":
			pixmap = QPixmap("pics/start.png")
			node = StartNode(id, pixmap.width(), pixmap.height(), scene)
		elif nodeType == "variable_update":
			pixmap = QPixmap("pics/variable_update.png")
			node = VariableUpdateNode(id, pixmap.width(), pixmap.height(), scene)
			updates = data[i]["variables"]
			[node.variableUpdates.append([k, data[i]["variables"][k]]) for k in updates.keys()]
			if len(node.variableUpdates) > 0:
				node.labelText = node.variableUpdates[0][0] + "=" + node.variableUpdates[0][1]
				if len(node.variableUpdates) > 1:
					node.labelText += " plus more"
		elif nodeType == "variable_decision":
			pixmap = QPixmap("pics/variable_decision.png")
			node = VariableDecisionNode(id, pixmap.width(), pixmap.height(), scene)
			output_conns = [x for x in data[i]["connectors"] if x["type"] == "condition_output"]
			if len(output_conns) > 0:
				node.labelText = output_conns[0]["condition"]["target"]
		elif nodeType == "random_decision":
			pixmap = QPixmap("pics/random_decision.png")
			node = RandomDecisionNode(id, pixmap.width(), pixmap.height(), scene)
			node.num_decisions = data[i]["number decisions"]
		elif nodeType == "gpt_decision":
			pixmap = QPixmap("pics/gpt_decision.png")
			node = GPTDecisionNode(id, pixmap.width(), pixmap.height(), scene)
			node.labelText = data[i]["label"]
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
		elif nodeType == "gemini_decision":
			pixmap = QPixmap("pics/gemini_decision.png")
			node = GeminiDecisionNode(id, pixmap.width(), pixmap.height(), scene)
			node.labelText = data[i]["label"]
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
		elif nodeType == "lmstudio_decision":
			pixmap = QPixmap("pics/lmstudio_decision.png")
			node = LMStudioDecisionNode(id, pixmap.width(), pixmap.height(), scene)
			node.labelText = data[i]["label"]
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
		elif nodeType == "turn_based_decision":
			pixmap = QPixmap("pics/turn_based_decision.png")
			node = TurnBasedDecisionNode(id, pixmap.width(), pixmap.height(), scene)
		elif nodeType == "wait":
			pixmap = QPixmap("pics/wait.png")
			node = WaitNode(id, pixmap.width(), pixmap.height(), scene)
			node.wait_time = data[i]["wait time"]
			node.labelText = "Wait " + str(node.wait_time) + "ms"
		elif nodeType == "timer":
			pixmap = QPixmap("pics/timer.png")
			node = TimerNode(id, pixmap.width(), pixmap.height(), scene)
			node.timerTime = data[i]["timer time"]
			node.labelText = "Timer " + str(node.timerTime) + " seconds"
		elif nodeType == "app_start":
			pixmap = QPixmap("pics/app_start.png")
			node = AppStartNode(id, pixmap.width(), pixmap.height(), scene)
			node.appName = data[i]["app"]
			node.labelText = node.appName
		elif nodeType == "tts_parameters":
			pixmap = QPixmap("pics/tts_parameters.png")
			node = TTSParameterNode(id, pixmap.width(), pixmap.height(), scene)
			node.parameters = data[i]["parameters"]
		elif nodeType == "gpt_variable":
			pixmap = QPixmap("pics/gpt_variable.png")
			node = GPTVariableUpdateNode(id, pixmap.width(), pixmap.height(), scene)
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
			node.variable = data[i]["variable"]
			node.labelText = data[i]["label"]
		elif nodeType == "gemini_variable":
			pixmap = QPixmap("pics/gemini_variable.png")
			node = GeminiVariableUpdateNode(id, pixmap.width(), pixmap.height(), scene)
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
			node.variable = data[i]["variable"]
			node.labelText = data[i]["label"]
		elif nodeType == "lmstudio_variable":
			pixmap = QPixmap("pics/lmstudio_variable.png")
			node = LMStudioVariableUpdateNode(id, pixmap.width(), pixmap.height(), scene)
			promptInfo = data[i]["prompt"]
			prompt = DialogPrompt(promptInfo["text prompt"], promptInfo["speakers"], promptInfo["history"], promptInfo["turns"])
			node.prompt = prompt
			node.variable = data[i]["variable"]
			node.labelText = data[i]["label"]
		elif nodeType == "function":
			pixmap = QPixmap("pics/python_function.png")
			node = PythonFunctionNode(id, pixmap.width(), pixmap.height(), scene)
			node.functionName = data[i]["function name"]
			node.variable = data[i]["variable"]
			node.labelText = node.functionName		
		elif nodeType == "enter_subseq":
			pixmap = QPixmap("pics/enter_subseq.png")
			node = EnterSubsequenceNode(id, pixmap.width(), pixmap.height(), scene)
			node.subseqName = data[i]["subsequence name"]
			node.labelText = node.subseqName
		elif nodeType == "reset_variables":
			pixmap = QPixmap("pics/reset_variables.png")
			node = ResetVariableNode(id, pixmap.width(), pixmap.height(), scene)
		elif nodeType == "send_to_dm":
			pixmap = QPixmap("pics/send_to_dm.png")
			node = SendToDMNode(id, pixmap.width(), pixmap.height(), scene)
			node.message_dict = data[i]["message_dict"]
			node.message = data[i]["message"]
			node.labelText = data[i]["label"]
		else:
			print("Unknown node type, ignoring...", nodeType)
			continue

		scene.placeNode(node, pixmap, xpos, ypos)
		node.set_type(nodeType)


		# self.view.centerOn(node)
		connectors = data[i]["connectors"]

		#add labels
		node.updateDialogLabel()

		#add connectors
		for conn in connectors:
			relX = conn["relX"]
			relY = conn["relY"]
			nodeType = conn["type"]
			connector = node.addConnector(xpos, ypos, relX, relY, nodeType)
			if nodeType == "condition_output":
				try: #single condition
					conditionData = conn["condition"]
					target = conditionData["target"]
					comparator = conditionData["comparator"]
					value = conditionData["value"]
					varType = conditionData["type"]
					cond = Condition()
					cond.updateCondition(target, comparator, value, varType)
					connector.condition = cond
				except KeyError: #multi condition
					multicond = MultiCondition()
					c = []
					for k in conn["condition"]:
						cond = Condition()
						conditionData = conn["condition"][k]
						target = conditionData["target"]
						comparator = conditionData["comparator"]
						value = conditionData["value"]
						varType = conditionData["type"]
						cond.updateCondition(target, comparator, value, varType)
						c.append(cond)
					multicond.conditions = c
					connector.condition = multicond
			try:
				inputID = conn["connectedNodeID"]
				connectionPairs.append([connector, inputID])
			except KeyError:
				pass

	#add connection lines
	for i in connectionPairs:
		if i[1] == None:
			continue

		inputNode = scene.getNodeGivenID(i[1])
		inputJoint = scene.getInputJointOfNode(inputNode)
		outputJoint = i[0]
		connectorLine = ConnectorLine(scene, outputJoint, inputJoint)
		if inputJoint == None:
			continue
		connectorLine.setLine(outputJoint.pos().x() + 5, outputJoint.pos().y() + 5, inputJoint.pos().x() + 5, inputJoint.pos().y() + 5)
		inputJoint.addConnectorLine(connectorLine)
		inputJoint.addOutputJoint(outputJoint)
		outputJoint.connectedInputJoint = inputJoint
		outputJoint.connectorLine = connectorLine
		scene.addItem(connectorLine)
			
	#updates max IDs over entire script
	for s in window.subwindows:
		if s.idctr > maxID:
			maxID = s.idctr

	window.setIDCounter(maxID + 1)
	scene.minX = minX
	scene.minY = minY
	scene.maxX = maxX
	scene.maxY = maxY
	scene.updateSceneRect()
	scene.setSceneChanged(False)