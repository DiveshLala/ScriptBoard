import window_classes.variable_update_window as variable_update
import window_classes.variable_decision_window as variable_decision
from condition import Condition, checkbool
from node_connections import ConditionOutputJoint, OutputJoint
from script_processor import get_string_between_brackets
from nodes.basic_nodes import DialogNode

class VariableUpdateNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(VariableUpdateNode, self).__init__(id, width, height, parent_scene)
		self.variableUpdates = []

	def mouseDoubleClickEvent(self, e):
		#no variables
		if len(self.parent_scene.getVariables()) == 0:
			return
		
		dlg = variable_update.VariableUpdateWindow(self.variableUpdates, self.parent_scene.getVariables(), self.parent_scene.getEnvironment())
		accept = dlg.exec()
		if accept == 1:
			self.variableUpdates = dlg.updates
			self.parent_scene.setSceneChanged(True)
			if len(self.variableUpdates) > 0:
				self.labelText = self.variableUpdates[0][0] + "=" + self.variableUpdates[0][1]
				if len(self.variableUpdates) > 1:
					self.labelText += " plus more"
			self.updateDialogLabel()

	
	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "variable_update"
		variables = {}
		for v in self.variableUpdates:
			variables[v[0]] = v[1]
		infoDict["variables"] = variables
		return infoDict

class VariableDecisionNode(DialogNode):

	def __init__(self, id, width, height, parent_scene):
		super(VariableDecisionNode, self).__init__(id, width, height, parent_scene)
	

	def mouseDoubleClickEvent(self, e):

		variables = self.parent_scene.getVariables()
		if len(variables) == 0:
			return

		dlg = variable_decision.VariableDecisionWindow([c.condition for c in self.connectors if isinstance(c, ConditionOutputJoint) and c.condition.comparator != "is other"], self.parent_scene.getVariables())
		accept = dlg.exec()

		if accept == 1:
			newConditions = dlg.conditions
			
			#add other to new conditions
			if len(newConditions) > 0:
				var_name = get_string_between_brackets(newConditions[0].targetObject)
				for v in self.parent_scene.getVariables():
					if v[0] == var_name:
						var_type = v[1]
						break
				else_cond = Condition()
				if var_type == "Boolean":
					else_cond.updateCondition("Variable(" + var_name + ")", "is", not checkbool(newConditions[0].compareValue), var_type)
				else:
					else_cond.updateCondition("Variable(" + var_name + ")", "is other", "", var_type)
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
						
			if len(tempConnectors) > 0:
				self.labelText = "Decision\n" + get_string_between_brackets(tempConnectors[0].condition.targetObject)
			else:
				self.labelText = ""

			inputConnectors = [c for c in self.connectors if not isinstance(c, OutputJoint)]
			self.connectors = inputConnectors + tempConnectors
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "variable_decision"
		return infoDict


class ResetVariableNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(ResetVariableNode, self).__init__(id, width, height, parent_scene)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "reset_variables"
		return infoDict