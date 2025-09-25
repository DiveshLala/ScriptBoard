import window_classes.utility_window as utility
from node_connections import *
from nodes.basic_nodes import DialogNode


class TimerNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(TimerNode, self).__init__(id, width, height, parent_scene)
		self.timerTime = 1

	def mouseDoubleClickEvent(self, e):
		dlg = utility.TimerWindow(self.timerTime)
		accept = dlg.exec()
		if accept:
			self.timerTime = dlg.timerTime.value()
			self.labelText = "Timer " + str(self.timerTime) + " seconds"
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)


	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "timer"
		infoDict["timer time"] = self.timerTime
		return infoDict


class WaitNode(DialogNode):
	def __init__(self, id, width, height, parent_scene):
		super(WaitNode, self).__init__(id, width, height, parent_scene)
		self.wait_time = 0


	def mouseDoubleClickEvent(self, e):
		dlg = utility.WaitWindow(self.wait_time)
		accept = dlg.exec()
		if accept:
			self.wait_time = dlg.waitTime.value()
			self.labelText = "Wait " + str(self.wait_time) + "ms"
			self.updateDialogLabel()
			self.parent_scene.setSceneChanged(True)

	def retrieveInfo(self):
		infoDict = super().retrieveInfo()
		infoDict["type"] = "wait"
		infoDict["wait time"] = self.wait_time
		return infoDict
