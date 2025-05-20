from icons import OutputJoint, InputJoint

class ClipBoard:

	def __init__(self):
		self.copiedNodes = None
		self.copiedSource = None	
		self.latestActions = []
	
	def undoAction(self, scene):
		sceneActions = [a for a in self.latestActions if a["scene"] == scene]
		if len(sceneActions) == 0:
			return
		action = sceneActions[-1]
		if action["type"] == "new node":
			node = action["object"]
			for c in node.connectors:
				action["scene"].removeItem(c)
			if node.displayedLabel != None:
				action["scene"].removeItem(node.displayedLabel)
			action["scene"].removeNode(action["object"])
		elif action["type"] == "new multiple nodes": #for pasting
			nodes = action["object"]
			for n in nodes:
				for c in n.connectors:
					#remove all pasted connector lines
					if isinstance(c,  OutputJoint) and c.connectorLine != None:
						action["scene"].removeItem(c.connectorLine)	
					#remove connector							
					action["scene"].removeItem(c)
				#remove label
				if n.displayedLabel != None:
					action["scene"].removeItem(n.displayedLabel)
				action["scene"].removeNode(n)
		elif action["type"] == "move node":
			node = action["object"]
			before = action["position"][0]
			node.moveNodeToCoordinates(before.x() + node.width/2, before.y() + node.height/2)
		elif action["type"] == "move multiple nodes":
			nodes = action["object"]
			before_positions = action["position"][0]
			for ind, n in enumerate(nodes):
				n.moveNodeToCoordinates(before_positions[ind].x() + n.width/2, before_positions[ind].y() + n.height/2)
		elif action["type"] == "new connector line":
			connectorLine = action["object"]
			connectorLine.remove()
		elif action["type"] == "delete node":
			node = action["object"]
			self.undoNodeDeletion(node, scene)
			self.undoConnectorDeletion(node, scene)
		elif action["type"] == "delete multiple nodes":
			nodes = action["object"]
			for n in nodes:
				self.undoNodeDeletion(n, scene)
			for n in nodes:
				self.undoConnectorDeletion(n, scene)
			scene.multipleSelected = True
					
		elif action["type"] == "delete connector line":
			connectorLine = action["object"]
			input_joint = action["position"][0]
			output_joint = action["position"][1]
			input_joint.addOutputJoint(output_joint)
			input_joint.addConnectorLine(connectorLine)
			scene.addItem(connectorLine)
		self.latestActions.remove(action)


	def undoNodeDeletion(self, node, scene):
		scene.placeNode(node, node.pixmap(), node.pos().x(), node.pos().y(), sceneCheck=True)
		#to ensure that the label gets refreshed...
		node.displayedLabel = None
		node.updateDialogLabel()
	
	def undoConnectorDeletion(self, node, scene):
		for conn in node.connectors:
			scene.addItem(conn)
			if isinstance(conn, InputJoint):
				for ind, joint in enumerate(conn.connectedOutputJoints):
					joint.connectedInputJoint = conn
					if conn.connectedOutputLines[ind] not in scene.items():
						scene.addItem(conn.connectedOutputLines[ind])
			elif isinstance(conn, OutputJoint):
				if conn.connectedInputJoint != None:
					conn.connectedInputJoint.addOutputJoint(conn)
					conn.connectedInputJoint.addConnectorLine(conn.connectorLine)
					if conn.connectorLine not in scene.items():
						scene.addItem(conn.connectorLine)
