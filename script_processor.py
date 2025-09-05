import os
import json
import time
import re
from prompt import DialogPrompt
from condition import checkbool
import random 
import importlib
from itertools import cycle

class ScriptProcessor:

	def __init__(self, parent):
		filename = parent.filename

		with open(filename, encoding="utf-8") as f:
			self.script_data = json.load(f)
		self.variable_dict = {}
		self.initialize_variables()
		self.server = parent.server
		self.llm_client = parent.llm_client
		self.parent_window = parent
		self.viewing_window = self.parent_window
		self.server.set_processor(self)
		self.received_robot_utterance = ""
		self.current_user_silence = 0
		self.current_turn = None
		self.current_turntaker = None
		self.timer_start = None
		self.timer_threshold = 0
		self.appRunning = False
		self.bargeInFlag = False
		self.isDoingBargeIn = False

		self.dialog_history = []

		self.users = []
		self.target_user = None
		for x in parent.environment:
			user = User(x[0])
			self.users.append(user)
			if x[1] == True:
				self.target_user = user
		
		self.parent_window.createMonitoringWindow(self.variable_dict)

	def initialize_variables(self):
		for x in self.script_data:
			if x.startswith("Variable"):
				name = self.script_data[x]["name"]
				t = self.script_data[x]["type"]
				val = self.script_data[x]["value"]
				print(self.script_data[x])
				if t == "Int":
					val = int(val)
				elif t == "Float":
					val = float(val)
				elif t == "Boolean":
					val = checkbool(val)
				else:
					val = str(val)
				self.variable_dict[name] = [t, val]
		print("Variable list: ", self.variable_dict)
		
	def start(self, start_node_id):
		self.process(start_node_id)
		self.close_monitoring_window()
		if self.parent_window.scriptRunning:
			self.parent_window.stopScript()
		print("Script finished")


	def reset(self):
		self.initialize_variables()
		self.received_robot_utterance = ""
		self.current_user_silence = 0
		self.current_turn = None
		self.timer_start = None
		self.timer_threshold = 0
		self.appRunning = False
		self.bargeInFlag = False

		self.dialog_history = []

		self.users = []
		self.target_user = None
		for x in self.parent_window.environment:
			user = User(x[0])
			self.users.append(user)
			if x[1] == True:
				self.target_user = user
		
		self.update_monitoring_window()

				
	def process(self, node_id, is_start=True):

		while True:

			if node_id == None:
				print("No nodes left to process, finishing...")
				return
			
			node = self.get_node_from_ID(node_id)

			print("Entering", node["type"], node_id)
			self.centerNode(node_id, 0.15)

			if node["type"] == "start":
				output_node_id = self.get_output_node_id(node)
				node_id = output_node_id
			elif node["type"] == "robot":
				output_node_id = self.get_output_node_id(node)
				dialog = node["dialog"].strip()
				tag = node["tag"]
				emotion = node["emotion"]
				gesture = node["gesture"]
				gaze = node["gaze"]
				barge_in = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "condition_output" and c["condition"]["target"] == "Barge-in"]

				if len(barge_in) > 0 and not self.isDoingBargeIn:
					self.isDoingBargeIn = True
				elif len(barge_in) == 0 and self.isDoingBargeIn:
					self.isDoingBargeIn = False

				gaze_id = self.get_gaze_id(gaze)

				if "Variable(" in dialog:
					for var in self.variable_dict.keys():
						if self.variable_dict[var][0] == "Boolean":
							continue
						dialog = dialog.replace("Variable(" + var + ")", str(self.variable_dict[var][1]))

				if len(dialog) > 0:
					self.send_message_to_server(utterance_message(dialog, tag, emotion, gesture, gaze_id))
					self.sent_robot_utterance = dialog
					barged = False
					while len(self.received_robot_utterance.strip()) == 0:
						if not self.parent_window.scriptRunning:
							print("Script stopped")
							return
						#check for barge in
						if len(barge_in) > 0 and self.bargeInFlag:
							output_node_id = barge_in[0]
							barged = True
							self.bargeInFlag = False
							break
						#if there is a tag, then cannot compare, so only check for non-blank utterances
						if len(tag) > 0 and len(self.received_robot_utterance.strip()) > 0:
							print("moving on...")
							break
						time.sleep(0.01)

					#update dialog history with what the robot actually said
					if barged:
						print("(USER BARGE IN)", dialog.strip())
						while len(self.received_robot_utterance.strip()) == 0 or not dialog.strip().startswith(self.received_robot_utterance.strip()):
							time.sleep(0.01)
						print("Robot said", self.received_robot_utterance.strip())
						self.dialog_history.append(["ROBOT", self.received_robot_utterance.strip()])
						self.update_monitoring_window()
						break
					else:
						print("Robot said", self.received_robot_utterance.strip())
						self.dialog_history.append(["ROBOT", dialog])
						self.update_monitoring_window()

				self.received_robot_utterance = ""
				node_id = output_node_id
			elif node["type"] == "human":
				#if all the connector outputs go nowhere then the script is finished, return None
				node_outputs = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "condition_output"]
				if all(v is None for v in node_outputs):
					node_id = None
				else:
					next_node_id = -1
					silence_node_info = self.get_silence_condition(node)
					timer_node_info = self.get_timer_condition(node)
					while True:
						time.sleep(0.1)

						if not self.parent_window.scriptRunning:
							print("Script stopped")
							return
						
						#timer condition
						if timer_node_info[0] == True and self.timer_start != None:
							if (time.time() - self.timer_start) > self.timer_threshold:
								next_node_id = timer_node_info[1]
								break

						#silence condition
						if silence_node_info[1] != None and self.current_user_silence > silence_node_info[0]:
							next_node_id = silence_node_info[1]
							break

						next_node_id = self.check_for_human_dialog_conditions(node)
						if next_node_id >= 0:
							break
						elif next_node_id == None: # none of the outputs are connected so the script will finish
							break
					node_id = next_node_id
			elif node["type"] == "variable_update":
				output_node_id = self.get_output_node_id(node)
				for var in node["variables"].keys():
					try:
						old_val = self.variable_dict[var][1]
						new_val = node["variables"][var]

						if new_val.startswith("Variable"):
							var_type = self.variable_dict[var][0]
							#string type so must be an append
							if var_type == "String":
								new_val = self.get_value_from_variable_string_append(new_val)
							#non string so is a formula
							else:
								new_val = self.get_value_from_variable_string_formula(new_val)
						
						if new_val != None:	
							if self.variable_dict[var][0] == "Int":
								new_val = int(new_val)
							elif self.variable_dict[var][0] == "Float":
								new_val = float(new_val)
							elif self.variable_dict[var][0] == "Boolean":
								new_val = checkbool(new_val)
								
							self.variable_dict[var][1] = new_val
							print("updated", var, "from", old_val, "to", new_val)
					except KeyError as e:
						print(e)
				self.update_monitoring_window()
				node_id = output_node_id
			elif node["type"] == "variable_decision":
				node_outputs = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "condition_output"]
				if len(node_outputs) == 0:
					return
				
				if all(v is None for v in node_outputs):
					node_id = None
				else:
					if not self.parent_window.scriptRunning:
						print("Script stopped")
						return
					
					next_node_id = self.check_variable_decision_conditions(node)

					if next_node_id == None: # none of the outputs are connected so the script will finish
						return
					else:
						node_id = next_node_id
			elif node["type"] == "human_target":
				output_node_id = self.get_output_node_id(node)
				new_target = node["new target"]
				if new_target.startswith("Human"):
					new_id = int(new_target.replace("Human ", ""))
					self.target_user = self.get_user_with_id(new_id)
				elif new_target == None:
					self.target_user = None
				elif new_target == "Non-target random":
					self.target_user = self.get_random_non_target_user()
				elif new_target == "Any random":
					self.target_user = self.get_random_user()

				if self.target_user == None:
					print("New target is None")
				else:
					print("New target is ", self.target_user.id)
				node_id = output_node_id
			elif node["type"] == "wait":
				output_node_id = self.get_output_node_id(node)
				wait_time = int(node["wait time"]) / 1000
				start_time = time.time()
				elapsed = 0
				print("waiting for ", wait_time, "seconds")
				while elapsed < wait_time:
					time.sleep(0.1)
					if not self.parent_window.scriptRunning:
						print("Script stopped")
						return
					elapsed = time.time() - start_time
				node_id = output_node_id
			elif node["type"] == "random_decision":
				node_outputs = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "output"]
				if len(node_outputs) == 0:
					return
				output_node_id = random.choice(node_outputs)
				node_id = output_node_id
			elif node["type"] == "robot_gpt" or node["type"] == "robot_gemini" or node["type"] == "robot_lmstudio":
				output_node_id = self.get_output_node_id(node)
				barge_in = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "condition_output" and c["condition"]["target"] == "Barge-in"]
				gaze = node["gaze"]

				if len(barge_in) > 0 and not self.isDoingBargeIn:
					self.isDoingBargeIn = True
				elif len(barge_in) == 0 and self.isDoingBargeIn:
					self.isDoingBargeIn = False
				
				prompt_info = node["prompt"]
				x = DialogPrompt(prompt_info["text prompt"], prompt_info["speakers"], prompt_info["history"], prompt_info["turns"])
				x.parseVariables(self.variable_dict)
				prompt = self.create_llm_prompt(x)
				if node["type"] == "robot_gpt":
					self.send_message_to_llm_client(llm_message(prompt, "gpt", recv_type="stream"))
				elif node["type"] == "robot_gemini":
					self.send_message_to_llm_client(llm_message(prompt, "gemini", recv_type="stream"))
				elif node["type"] == "robot_lmstudio":
					self.send_message_to_llm_client(llm_message(prompt, "lmstudio", recv_type="stream"))
				self.llm_client.streaming = True

				#gaze for each sentence
				gaze_id = self.get_gaze_id(gaze)

				if gaze_id == -1 and gaze == "Multiparty shift":
					gaze_targets = cycle([u.id for u in self.users])
				else:
					gaze_targets = cycle([gaze_id])

				while self.llm_client.streaming or len(self.llm_client.streamed_sentences) > 0:
					if len(self.llm_client.streamed_sentences) > 0:
						llm_response = self.llm_client.streamed_sentences[0]
						self.llm_client.streamed_sentences.pop(0)
						llm_response = llm_response.replace("\n", "")
						self.llm_client.response = ""
						time.sleep(0.1)
						barged = False

						gaze_target = next(gaze_targets)

						#if a failure message is received then continue to the next
						if llm_response == "FAIL_RESPONSE":
							# future work: use fallback utterance if there is a failure
							# self.send_message_to_server(utterance_message("そうですね", "", "", "", gaze_target))	
							self.update_monitoring_window()
							break

						self.send_message_to_server(utterance_message(llm_response, "", "", "", gaze_target))	

						while len(self.received_robot_utterance.strip()) == 0:
							#check for barge in
							if len(barge_in) > 0 and self.bargeInFlag:
								output_node_id = barge_in[0]
								barged = True
								self.bargeInFlag = False
								break
							if not self.parent_window.scriptRunning:
								print("Script stopped")
								return
							time.sleep(0.01)

						print("Robot said", self.received_robot_utterance.strip())
						self.received_robot_utterance = ""
						self.dialog_history.append(["ROBOT", llm_response])
						self.update_monitoring_window()
				self.received_robot_utterance = ""
				node_id = output_node_id
			elif node["type"] == "gpt_decision" or node["type"] == "gemini_decision" or node["type"] == "lmstudio_decision":
				node_outputs = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "condition_output"]
				if len(node_outputs) == 0:
					return
				
				if all(v is None for v in node_outputs):
					node_id = None
				else:
					prompt_info = node["prompt"]
					x = DialogPrompt(prompt_info["text prompt"], prompt_info["speakers"], prompt_info["history"], prompt_info["turns"])
					x.parseVariables(self.variable_dict)
					prompt = self.create_llm_prompt(x)
					if node["type"] == "gpt_decision":
						self.send_message_to_llm_client(llm_message(prompt, "gpt"))
					elif node["type"] == "gemini_decision":
						self.send_message_to_llm_client(llm_message(prompt, "gemini"))
					elif node["type"] == "lmstudio_decision":
						self.send_message_to_llm_client(llm_message(prompt, "lmstudio"))
					while self.llm_client.response == None or len(self.llm_client.response) == 0:
						time.sleep(0.1)
					llm_response = self.llm_client.response
					self.llm_client.response = ""
					next_node = None
					for c in node["connectors"]:
						if c["type"] == "condition_output":
							condition = c["condition"]
							outputID = c["connectedNodeID"]
							if outputID == None:
								continue

							if condition["comparator"] == "is other":
								next_node = outputID
								break

							comparator = condition["comparator"]
							value = condition["value"]
							var_type = condition["type"]

							if var_type == "String" and llm_response != None:
								if meets_string_condition(llm_response, comparator, value):
									next_node = outputID
									break
							elif var_type == "Numeric" and llm_response != None:
								value = float(value)
								try:
									llm_response = int(llm_response)
									if meets_numerical_condition(llm_response, comparator, value):
										next_node = outputID
										break
								except ValueError as e:
									continue
					node_id = next_node
			elif node["type"] == "turn_based_decision":
				node_outputs = [c["connectedNodeID"] for c in node["connectors"] if c["type"] == "condition_output"]
				if len(node_outputs) == 0:
					return
				
				if all(v is None for v in node_outputs):
					node_id = None
				else:
					if not self.parent_window.scriptRunning:
						print("Script stopped")
						return
					
					next_node_id = self.check_turn_based_decision_conditions(node)

					if next_node_id == None: # none of the outputs are connected so the script will finish
						return
					else:
						node_id = next_node_id

			elif node["type"] == "timer":
				print("Timer started")
				output_node_id = self.get_output_node_id(node)
				self.timer_start = time.time()
				self.timer_threshold = int(node["timer time"])
				node_id = output_node_id
			elif node["type"] == "tts_parameters":
				output_node_id = self.get_output_node_id(node)
				parameters = node["parameters"]
				for p in parameters:
					self.send_message_to_server(tts_parameter_message(p[0], p[1]))
					time.sleep(0.1)
				node_id = output_node_id
			elif node["type"] == "gpt_variable" or node["type"] == "gemini_variable" or node["type"] == "lmstudio_variable":
				output_node_id = self.get_output_node_id(node)
				prompt_info = node["prompt"]
				x = DialogPrompt(prompt_info["text prompt"], prompt_info["speakers"], prompt_info["history"], prompt_info["turns"])
				x.parseVariables(self.variable_dict)
				prompt = self.create_llm_prompt(x)
				if node["type"] == "gpt_variable":
					self.send_message_to_llm_client(llm_message(prompt, "gpt"))
				elif node["type"] == "gemini_variable":
					self.send_message_to_llm_client(llm_message(prompt, "gemini"))
				elif node["type"] == "lmstudio_variable":
					self.send_message_to_llm_client(llm_message(prompt, "lmstudio"))
				while self.llm_client.response == None or len(self.llm_client.response) == 0:
					time.sleep(0.1)
				print("LLM response", self.llm_client.response)
				llm_response = self.llm_client.response
				if llm_response != None:
					llm_response = llm_response.replace("\n", "")
					self.llm_client.response = ""
					variable = node["variable"]
					variableInfo = self.variable_dict[variable]
					try:
						if variableInfo[0] == "Int":
							self.variable_dict[variable][1] = int(llm_response)
						elif variableInfo[0] == "Float":
							self.variable_dict[variable][1] = float(llm_response)
						elif variableInfo[0] == "Boolean":
							if llm_response.lower() == "true":
								self.variable_dict[variable][1] = True
							elif llm_response.lower() == "false":
								self.variable_dict[variable][1] = False
						else:
							self.variable_dict[variable][1] = llm_response
						print("updated", self.variable_dict[variable])
					except ValueError as e:
						print(e)
						print("Could not update variable, wrong type!")
				else:
					print("No variables updated from LLM...")
				self.update_monitoring_window()
				node_id = output_node_id
			elif node["type"] == "function":
				output_node_id = self.get_output_node_id(node)
				func = node["function name"].replace(".py", "")
				variable_store = node["variable"]
				try:
					x = importlib.import_module("functions." + func)
					y = x.run(self)
					if len(variable_store) > 0:
						var = self.variable_dict[variable_store]
						var_type = var[0]
						try:			
							if var_type == "Int":
								new_val = int(y)
							elif var_type == "Float":
								new_val = float(y)
							elif var_type == "Boolean":
								new_val = checkbool(y)
							else:
								new_val = str(y)
								
							self.variable_dict[variable_store][1] = new_val
							print("updated", variable_store, "to", new_val)
						except ValueError as e:
							print("Could not update ", variable_store, "to", y)
				except AttributeError as e:
					print("Function does not have run() method, skipping...")
				except FileNotFoundError as e:
					print("No such function, skipping...")
				except Exception as e:
					print(e)
					print("Exception in function. Skipping...")
				self.update_monitoring_window()
				node_id = output_node_id
			elif node["type"] == "enter_subseq":
				output_node_id = self.get_output_node_id(node)
				subseq_name = node["subsequence name"]
				if len(subseq_name) > 0:
					subseq_start_id = self.get_subsequence_start_node_id(subseq_name)
					if subseq_start_id != None:
						print("Entering subsequence ", subseq_name)
						self.parent_window.getMainWindow().showWindow(subseq_name)
						self.viewing_window = self.parent_window.getMainWindow().getSubSequenceWindow(subseq_name)
						self.process(subseq_start_id)
						print("Ending subsequence...")
						self.parent_window.getMainWindow().getSubSequenceWindow(subseq_name).view.scale(0.5, 0.5)
						self.parent_window.getMainWindow().showWindow(self.parent_window.name)
						self.viewing_window = self.parent_window
				node_id = output_node_id
			elif node["type"] == "reset_variables":
				output_node_id = self.get_output_node_id(node)
				self.reset()
				node_id = output_node_id
			elif node["type"] == "send_to_dm":
				output_node_id = self.get_output_node_id(node)
				self.send_message_to_server(node["message"])
				node_id = output_node_id
			else:
				print("Entering ", node_id)
		# print("Node", node_id, "finished")


	def get_silence_condition(self, node):
		for c in node["connectors"]:
			if c["type"] == "condition_output":
				try:
					target = c["condition"]["target"]
					if target == "Silence time":
						value = c["condition"]["value"]
						return (value, c["connectedNodeID"])
				except KeyError as e:
					continue
		return (None, None)
	
	def get_timer_condition(self, node):
		for c in node["connectors"]:
			if c["type"] == "condition_output":
				try:
					target = c["condition"]["target"]
					if target == "Timer":
						return (True, c["connectedNodeID"])
				except KeyError as e:
					continue
		return (None, None)
	

	def get_value_from_variable_string_formula(self, formula):
		var_name = get_string_between_brackets(formula)
		try:
			value = self.variable_dict[var_name][1]
		except KeyError as e:
			print("Variable does not exist!")
			return None

		if "+" in formula:
			return value + float(formula.split("+")[1])
		elif "-" in formula:
			return value - float(formula.split("-")[1])
		elif "*" in formula:
			return value * float(formula.split("*")[1])
		elif "/" in formula:
			return value / float(formula.split("/")[1])
		return None
	
	def get_value_from_variable_string_append(self, formula):
		var_name = get_string_between_brackets(formula)
		try:
			value = self.variable_dict[var_name][1]
		except KeyError as e:
			print("Variable does not exist!")
			return None
		
		appended = formula.split("+")[1]

		if appended == "Target's utterance":
			return value + self.get_target_user().current_user_ipu
		elif appended == "Target's turn":
			return value + self.get_target_user().latest_user_turn_utterance
		elif appended.startswith("Human") and appended.endswith("utterance"):
			hid = int(appended.replace("Human", "").replace("utterance", ""))
			return value + self.get_user_with_id(hid).current_user_ipu
		elif appended.startswith("Human") and appended.endswith("turn"):
			hid = int(appended.replace("Human", "").replace("turn", ""))
			return value + self.get_user_with_id(hid).latest_user_turn_utterance

	def check_for_new_dialog(self):
		for u in self.users:
			if u.asr_checked == False:
				return True
		return False

	def check_for_human_dialog_conditions(self, node):

		target_utterance = ""
		target_turn_utterance = ""
		if self.get_target_user() != None: 
			if self.get_target_user().asr_checked == False:
				target_utterance = self.get_target_user().current_user_ipu
			if self.get_target_user().turn_checked == False:
				target_turn_utterance = self.get_target_user().latest_user_turn_utterance
		
		non_target_utterances = []
		non_target_turn_utterances = []
		for u in self.get_non_target_users():
			if u.asr_checked == False:
				non_target_utterances.append(u.current_user_ipu)
			if u.turn_checked == False:
				non_target_turn_utterances.append(u.latest_user_turn_utterance)
		
		all_utterances = []
		all_turn_utterances = []
		for u in self.users:
			if u.asr_checked == False:
				all_utterances.append(u.current_user_ipu)
			if u.turn_checked == False:
				all_turn_utterances.append(u.latest_user_turn_utterance)
		
		output_node_ID = -1

		for c in node["connectors"]:
			if c["type"] == "condition_output":
				condition = c["condition"]
				outputID = c["connectedNodeID"]
				if outputID == None:
					continue
				try:
					target = condition["target"]
					comparator = condition["comparator"]
					value = condition["value"]
					#variable condition
					if target.startswith("Variable"):
						if self.meets_variable_condition(target, comparator, value):
							output_node_ID = outputID
							break
					#human id utterance
					elif target.startswith("Human"):
						hid = int(target.replace("Human", "").replace("utterance", ""))
						user = self.get_user_with_id(hid)
						if user == None:
							continue
						target_utterance = user.current_user_ipu
						if len(target_utterance) > 0 and user.asr_checked == False:
							meets_condition = meets_string_condition(target_utterance, comparator, value)
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break
					#targets utterance
					elif target == "Target's utterance":
						if len(target_utterance) > 0:
							meets_condition = meets_string_condition(target_utterance, comparator, value)
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break
					#targets turn
					elif target == "Target's turn":
						if target_turn_utterance == None:
							continue
						if len(target_turn_utterance) > 0:
							meets_condition = meets_string_condition(target_turn_utterance, comparator, value)
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break
					#non-target's utterance
					elif target == "Non-target's utterance":
						for utt in non_target_utterances:
							meets_condition = meets_string_condition(utt, comparator, value)
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break
					#non-target's turn
					elif target == "Non-target's turn":
						for utt in non_target_turn_utterances:
							if utt == None:
								continue
							meets_condition = meets_string_condition(utt, comparator, value)
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break
					#anyone's utterance
					elif target == "Anyone's utterance":
						for utt in all_utterances:
							meets_condition = meets_string_condition(utt, comparator, value)
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break
					#anyone's turn
					elif target == "Anyone's turn":
						for utt in all_turn_utterances:
							if utt == None:
								continue
							meets_condition = meets_string_condition(utt, comparator, value)
							# self.get_target_user().turn_checked = True
							if meets_condition:
								print("Condition met!", target, comparator, value)
								output_node_ID = outputID
								break

				except KeyError:
					#multi conditional
					cond_met = True
					for cond in condition:
						target = condition[cond]["target"]
						comparator = condition[cond]["comparator"]
						value = condition[cond]["value"]
						if target.startswith("Variable"):
							if not self.meets_variable_condition(target, comparator, value):
								cond_met = False
								break
						elif target == "Target's utterance":
							if len(target_utterance) > 0:
								if not meets_string_condition(target_utterance, comparator, value):
									cond_met = False
									break
							else:
								cond_met = False
						elif target == "Target's turn":
							if target_turn_utterance == None:
								cond_met = False
								break
							if len(target_turn_utterance) > 0:
								if not meets_string_condition(target_turn_utterance, comparator, value):
									cond_met = False
									break
							else:
								cond_met = False
								break
						elif target == "Non-target's utterance":
							if len(non_target_utterances) > 0:
								cond_met = False
								break
							for utt in self.non_target_utterances:
								if not meets_string_condition(utt, comparator, value):
									cond_met = False
									break
						elif target == "Non-target's turn":
							if len(non_target_turn_utterances) > 0:
								cond_met = False
								break
							if utt in non_target_turn_utterances:
								if utt == None:
									cond_met = False
									break
								if not meets_string_condition(utt, comparator, value):
									cond_met = False
									break
						elif target == "Anyone's utterance":
							if len(all_utterances) > 0:
								cond_met = False
								break
							if utt in all_utterances:
								if not meets_string_condition(utt, comparator, value):
									cond_met = False
									break

						elif target == "Anyone's turn":
							if len(all_turn_utterances) > 0:
								cond_met = False
								break
							if utt in all_turn_utterances:
								if utt == None or len(utt) == 0:
									cond_met = False
									break
								if not meets_string_condition(utt, comparator, value):
									cond_met = False
									break
					if cond_met:
						print("Multi-condition met!", [str(condition[cond]["target"]) + str(condition[cond]["comparator"]) + str(condition[cond]["value"]) for cond in condition])
						output_node_ID = outputID
						break
				
		for u in self.users:
			u.asr_checked = True
			u.turn_checked = True
		
		return output_node_ID
	
	def get_gaze_id(self, gaze_type):
		gaze_id = -1
		if gaze_type == "Target":
			gaze_id = self.get_target_user().id
		elif gaze_type == "Non-target first":
			for x in self.users:
				if x != self.get_target_user():
					gaze_id = x.id
					break
		elif gaze_type == "Non-target random":
			non_target_users = [x for x in self.users if x != self.get_target_user()]
			gaze_id = random.choice(non_target_users).id
		elif gaze_type == "Any random":
			gaze_id = random.choice(self.users).id
		elif gaze_type.startswith("Human"):
			gaze_id = int(gaze_type.replace("Human", ""))
		elif gaze_type == "No target":
			gaze_id = "No target"
		return gaze_id

	def check_variable_decision_conditions(self, node):

		for c in node["connectors"]:
			if c["type"] == "condition_output":
				condition = c["condition"]
				outputID = c["connectedNodeID"]
				
				if condition["comparator"] == "is other":
					return outputID
				
				if self.meets_variable_condition(condition["target"], condition["comparator"], condition["value"]):
					return outputID
		
	def check_turn_based_decision_conditions(self, node):

		for c in node["connectors"]:
			if c["type"] == "condition_output":
				condition = c["condition"]
				outputID = c["connectedNodeID"]
				
				if condition["comparator"] == "is other":
					return outputID
				
				turn_state = condition["value"]

				if turn_state == "Offer to human" and self.current_turn == "OFFER_TO_HUMAN":
					return outputID
				elif turn_state == "Human" and self.current_turn == "HUMAN_TURN":
					return outputID
				elif turn_state == "Robot" and self.current_turn == "ROBOT_TURN":
					return outputID
				elif turn_state == "Offer to robot" and self.current_turn == "OFFER_TO_ROBOT":
					return outputID

	def meets_variable_condition(self, target, comparator, value):

		var_name = re.search(r"\(([A-Za-z0-9_]+)\)", target).group(1)
		var_value = self.variable_dict[var_name][1]
		var_type = self.variable_dict[var_name][0]
		if (var_type == "Int" or var_type == "Float") and meets_numerical_condition(var_value, comparator, float(value)):
			return True
		elif var_type == "String" and meets_string_condition(var_value, comparator, value):
			return True
		elif var_type == "Boolean" and meets_boolean_condition(var_value, value):
			return True
		return False		

	def get_target_user(self):
		if self.target_user == None:
			return None
		for user in self.users:
			if self.target_user == user:
				return user
		return None
	
	def get_user_with_id(self, id):
		for x in self.users:
			if id == x.id:
				return x
		return None

	def get_non_target_users(self):
		non_target_users = []
		for user in self.users:
			if self.target_user != user:
				non_target_users.append(user)
		return non_target_users

	def get_random_user(self):
		return random.choice(self.users)
	
	def get_random_non_target_user(self):
		return random.choice(self.get_non_target_users())
	
	def get_output_node_id(self, node_info):
		conn_info = node_info["connectors"]
		for x in conn_info:
			if x["type"] == "output":
				return x["connectedNodeID"]
		return None

	def get_node_from_ID(self, id):
		for x in self.script_data:
			if x.startswith("Node"): 
				if self.script_data[x]["id"] == id:
					return self.script_data[x]
			elif x.startswith("Subsequence"):
				nodes = self.script_data[x]["nodes"]
				for y in nodes:
					if y.startswith("Node"):
						if nodes[y]["id"] == id:
							return nodes[y]
	
	def get_subsequence_start_node_id(self, subseq_name):
		for x in self.script_data:
			if x.startswith("Subsequence"):
				if self.script_data[x]["name"] != subseq_name:
					continue
				nodes = self.script_data[x]["nodes"]
				for y in nodes:
					if y.startswith("Node"):
						if nodes[y]["type"] == "start":
							return nodes[y]["id"]



	
	def message_notification(self, message):

		if message["type"] == "turn":
			prev_turn = self.current_turn
			self.current_turn = message["turn state"]
			if self.current_turn == "OFFER_TO_ROBOT":
				for user in self.users:
					user.end_turn()
			elif self.current_turn == "ROBOT_TURN":
				self.current_turntaker = "Robot"
				self.current_user_silence = 0
				for user in self.users:
					user.reset_turn()
			elif self.current_turn == "HUMAN_TURN":
				try:
					x = int(message["human id"])
					if prev_turn == "HUMAN_TURN" and self.current_turntaker != x:
						self.get_user_with_id(self.current_turntaker).end_turn()
						print("new turntaker", self.current_turntaker)
					self.current_turntaker = x
				except ValueError as e:
					pass
		elif message["type"] == "asr":
			utterance = message["utterance"]
			human_id = int(message["human id"])
			if self.current_turn != "ROBOT_TURN":
				self.dialog_history.append(["HUMAN " + str(human_id), utterance])
				for user in self.users:
					if user.id == human_id:
						user.update_asr(utterance)
				self.update_monitoring_window()
		elif message["type"] == "robot stop speech":
			utterance = message["utterance"]
			self.received_robot_utterance = utterance
		elif message["type"] == "silence time":
			self.current_user_silence = int(message["time"])
		elif message["type"] == "variable update":
			var_name = message["variable"]
			var_value = message["value"]
			old_val = self.variable_dict[var_name][1]

			try:			
				if self.variable_dict[var_name][0] == "Int":
					new_val = int(var_value)
				elif self.variable_dict[var_name][0] == "Float":
					new_val = float(var_value)
				elif self.variable_dict[var_name][0] == "Boolean":
					new_val = checkbool(var_value)
				else:
					new_val = str(var_value)
				self.variable_dict[var_name][1] = new_val
				print("updated", var_name, "from", old_val, "to", new_val)
			except ValueError as e:
				print("Could not update ", var_name, "to", var_value)
			self.update_monitoring_window()
		elif message["type"] == "barge in detected":
			self.bargeInFlag = True
		else:
			print("Unknown message", message)
		
	def create_llm_prompt(self, prompt):
		prompt_instruction = prompt.text_prompt
		speakers = prompt.speakers
		history = prompt.history
		num_turns = prompt.numTurns

		if speakers == "None":
			return prompt_instruction
		elif speakers == "All":
			speak_id = "All"
		elif speakers == "Users only":
			speak_id = "Users"
		elif speakers == "Target user only":
			speak_id = "Target"
		elif speakers == "Non-target user only":
			speak_id = "Non-target"
		elif speakers == "Robot only":
			speak_id = "Robot"
		elif speakers == "Target and Robot only":
			speak_id = "Target-and-Robot"

		if history == "Whole dialog history":
			return prompt_instruction + "\n" + self.create_history_script(speaker_id=speak_id)
		elif history == "Most recent turns":
			turns = int(num_turns)
			return prompt_instruction + "\n" + self.create_history_script(speaker_id=speak_id, num_recent_turns=turns)


	def create_history_script(self, speaker_id="All", num_recent_turns="All"):
		print("history")
		print(self.dialog_history)
		turn_based_script = self.merge_ipus(self.dialog_history)
		#the case of all users
		relevant_speakers = [x for x in turn_based_script]

		if speaker_id == "All":
			relevant_speakers = [x for x in relevant_speakers]
		elif speaker_id == "Users":
			relevant_speakers = [x for x in relevant_speakers if x[0].startswith("HUMAN")]
		elif speaker_id == "Robot":
			relevant_speakers = [x for x in relevant_speakers if x[0].startswith("ROBOT")]
		elif speaker_id == "Target":
			relevant_speakers = [x for x in relevant_speakers if x[0].startswith("HUMAN") and int(x[0].replace("HUMAN ", "")) == self.target_user.id]
		elif speaker_id == "Non-target":
			relevant_speakers = [x for x in relevant_speakers if x[0].startswith("HUMAN") and int(x[0].replace("HUMAN ", "")) != self.target_user.id]
		elif speaker_id == "Target-and-Robot":
			relevant_speakers = [x for x in relevant_speakers if x[0].startswith("HUMAN") and int(x[0].replace("HUMAN ", "")) == self.target_user.id or x[0].startswith("ROBOT")]

		if num_recent_turns != "All":
			relevant_speakers = relevant_speakers[-num_recent_turns:]

		#check how many speakers so we know whether to add other information
		num_human_speakers = set([x[0] for x in relevant_speakers if x[0].startswith("HUMAN")])
		script = ""
		for x in relevant_speakers:
			
			speaker_id = x[0]
			if len(num_human_speakers) == 1 and x[0].startswith("HUMAN"):
				speaker_id = "HUMAN"
				
			script += speaker_id + " " + x[1] + "\n"

		print("Script")
		print(script)
		return script
	
	def merge_ipus(self, history):
		cur_speaker = None
		cur_turn_utt = ""
		mod_hist = []
		for utt in history:
			speaker = utt[0]
			ipu = utt[1]
			if speaker != cur_speaker:
				if cur_speaker != None:
					mod_hist.append([cur_speaker, cur_turn_utt])
				cur_turn_utt = ""
			if is_string_English(ipu):
				ipu = " " + ipu
			cur_turn_utt += ipu
			cur_turn_utt = cur_turn_utt.strip()
			cur_speaker = speaker
		mod_hist.append([cur_speaker, cur_turn_utt])
		return mod_hist
	
	def send_message_to_server(self, message):
		self.server.send_message(message)

	def send_message_to_llm_client(self, message):
		self.llm_client.send_message(message)

	def update_monitoring_window(self):
		self.parent_window.doUpdate()
	
	def close_monitoring_window(self):
		self.parent_window.doUpdateCloseMonitoringWindow()
	
	def centerNode(self, node_id, scale):
		self.viewing_window.doCentering(node_id, scale)

class User:

	def __init__(self, user_id):
		self.id = user_id
		self.current_user_ipu = ""
		self.current_user_turn_utterance = ""
		self.latest_user_turn_utterance = None
		self.asr_checked = True
		self.turn_checked = True
	
	def update_asr(self, asr):
		self.current_user_ipu = asr
		#for now just assume ascii is english words
		english_asr = is_string_English(asr)
		if english_asr:
			self.current_user_turn_utterance = self.current_user_turn_utterance + " " + asr
		else:
			self.current_user_turn_utterance = self.current_user_turn_utterance + asr
		self.current_user_turn_utterance = self.current_user_turn_utterance.strip()
		self.asr_checked = False
		print("User" , str(self.id),  "said", asr)
		print("User", str(self.id),  "turn", self.current_user_turn_utterance)
	
	def end_turn(self):
		self.latest_user_turn_utterance = self.current_user_turn_utterance
		self.current_user_turn_utterance = ""
		self.turn_checked = False
	
	def reset_turn(self):
		print("TURN RESET")
		self.asr_checked = True
		self.turn_checked = True
		self.current_user_ipu = ""
		self.current_user_turn_utterance = ""
		self.latest_user_turn_utterance = None


#messaging
def utterance_message(utterance, tag, emotion, gesture, gaze_id):
	message = json.dumps({"type": "robot utterance", "utterance": utterance, "tag": tag, "emotion": emotion, "gesture": gesture, "gaze target": gaze_id})
	return message

def tts_parameter_message(parameter, value):
	message = json.dumps({"type": "tts parameter change", "parameter name": parameter, "value": value})
	return message

def llm_message(prompt, llm, recv_type="block"):
	message = json.dumps({"prompt": prompt, "type": recv_type, "llm": llm})
	return message

def get_string_between_brackets(s):
	return re.search(r"\(([A-Za-z0-9_]+)\)", s).group(1)

def meets_string_condition(x, comparator, value):

	print("Checking", x, comparator, value)

	if comparator == "character length greater than":
		return len(x) > int(value)
	elif comparator == "character length less than":
		return len(x) < int(value)
	elif comparator == "word length greater than":
		#English
		if is_string_English(x):
			return len(x.split(" ")) > int(value)
		else:
			return False
	elif comparator == "word length less than":
		#English
		if is_string_English(x):
			return len(x.split(" ")) < int(value)
		else:
			return False
	
	if value.startswith("Wordlist("):
		filename = get_string_between_brackets(value)
		values = []
		for l in os.listdir("./word_lists/"):
			if filename == l.replace(".words", ""):
				f = open("./word_lists/" + filename + ".words", "r", encoding="utf-8")
				[values.append(word.strip()) for word in f.readlines() if len(word) > 0]
				values = [v.lower() for v in values]
		if len(values) == 0:
			return False		
	else:
		value = value.replace("；", ";")
		values = value.split(";")
		values = [v.lower() for v in values]
	
	if comparator == "is anything":
		return len(x) > 0
	elif comparator == "equals":
		return any(item == x.lower() for item in values)
	elif comparator == "contains":
		return any(item in x.lower() for item in values)
	elif comparator == "contains word":
		x = x.lower()
		return any(item in x.split(" ") for item in values)
	elif comparator == "starts with":
		return any(x.lower().startswith(item) for item in values)
	elif comparator == "ends with":
		return any(x.lower().endswith(item) for item in values)
	elif comparator == "does not equal":
		return not x.lower() in values
	elif comparator == "does not contain":
		return not any(item in x.lower() for item in values)
	elif comparator == "does not start with":
		return not any(x.lower().startswith(item) for item in values)
	elif comparator == "does not end with":
		return not any(x.lower().endswith(item) for item in values)
	
	print("Can't test condition!", comparator)
	return False

def meets_numerical_condition(x, comparator, value):

	if comparator == "=":
		return x == value
	elif comparator == ">":
		return x > value
	elif comparator == "<":
		return x < value
	elif comparator == ">=":
		return x >= value
	elif comparator == "<=":
		return x <= value
	return False

def meets_boolean_condition(x, value):
	return x == value

def is_string_English(s):
	return s.isascii()
