import window_classes.utility_window as utility
import window_classes.turn_state_decision_window as turn_state_decision
from condition import Condition
from node_connections import OutputJoint, ConditionOutputJoint
from nodes.basic_nodes import DialogNode

class RandomDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(RandomDecisionNode, self).__init__(id, width, height, parent_scene)
		self.num_decisions = 1

	def mouseDoubleClickEvent(self, e):
		dlg = utility.RandomDecisionWindow(self.num_decisions)
		accept = dlg.exec()
		if accept:
			self.num_decisions = int(dlg.numDecisions.value())
			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			oldConnectors = [c for c in self.connectors if isinstance(c, OutputJoint)]

			#if new value is greater, shift the connectors up and add more
			if self.num_decisions > len(oldConnectors):

				for conn in oldConnectors:
					conn.relX = self.width + 2
					conn.relY = self.height/2 + offset
					conn.setPosition(nodeXPos + conn.relX, nodeYPos + conn.relY)
					tempConnectors.append(conn)
					conn.adjustConnectorLine()
					offset += 15
				
				for i in range(self.num_decisions - len(oldConnectors)):
					conn = self.addConnector(nodeXPos, nodeYPos, self.width + 2, self.height/2 + offset, "output")
					tempConnectors.append(conn)
					offset += 15
				
				inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
				self.connectors = inputConnectors + tempConnectors	
			
			#if new value is less, remove extra connectors			
			else:
				for i, conn in enumerate(oldConnectors):
					if self.num_decisions - i > 0:
						conn.relX = self.width + 2
						conn.relY = self.height/2 + offset
						conn.setPosition(nodeXPos + conn.relX, nodeYPos + conn.relY)
						tempConnectors.append(conn)
						conn.adjustConnectorLine()
						offset += 15
					else:
						conn.delete()
				inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
				self.connectors = inputConnectors + tempConnectors	
				
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "random_decision"
		infoDict["number decisions"] = self.num_decisions
		return infoDict

class TurnBasedDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(TurnBasedDecisionNode, self).__init__(id, width, height, parent_scene)
		self.conditions = []

	def mouseDoubleClickEvent(self, e):
		dlg = turn_state_decision.TurnStateDecisionWindow([c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.comparator != "is other"])
		accept = dlg.exec()

		if accept == 1:
			newConditions = dlg.conditions
			
			#add other to new conditions
			if len(newConditions) > 0:
				else_cond = Condition()
				else_cond.updateCondition("Turn state", "is other", "", "String")
				present = [n for n in newConditions if n.displayString() == else_cond.displayString()]
				if len(present) == 0:
					newConditions.append(else_cond)

			nodeXPos = self.sceneBoundingRect().getCoords()[0]
			nodeYPos = self.sceneBoundingRect().getCoords()[1]

			offset = -30
			tempConnectors = []
			for newCond in newConditions:
				matchingConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition == newCond]
				if len(matchingConnectors) == 0: #condition is a new one
					conn = self.addConnector(nodeXPos, nodeYPos, self.width + 2, self.height/2 + offset, "condition_output", condition=newCond)
					print("adding connector", newCond.displayString())
					tempConnectors.append(conn)
				else:	#condition already exists
					conn = matchingConnectors[0]
					conn.relX = self.width + 2
					conn.relY = self.height/2 + offset
					conn.setPosition(nodeXPos + conn.relX, nodeYPos + conn.relY)
					tempConnectors.append(conn)
					conn.adjustConnectorLine()
				offset += 15
			
			# #get rid of all connectors that have been deleted
			removedConnectors = [c for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.displayString() not in [tc.condition.displayString() for tc in tempConnectors]]

			for conn in removedConnectors:
				conn.delete()

			inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
			self.connectors = inputConnectors + tempConnectors
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "turn_based_decision"
		return infoDict

