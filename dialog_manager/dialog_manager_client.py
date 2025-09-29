import socket
import time
import traceback
import json
import threading
import dialog_manager_GUI as dmGUI
import sys

class DialogManagerClient:
	def __init__(self, host):
		self.HOST = host
		self.PORT = 5050
		self.soc = None
		self.connected = False

	def start_connecting(self):
		# Establishing a server with robust error handling
		RETRY_WAIT = 3
		while True:
			try:
				self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				while not self.connected:
					try:
						self.soc.connect((self.HOST, self.PORT))
						print('Connected to ScriptBoard server', self.HOST, self.PORT)
						self.connected = True
					except (ConnectionRefusedError, socket.timeout) as e:
						print(f"Connection failed: {e}. Retrying in {RETRY_WAIT}s...")
						time.sleep(RETRY_WAIT)
						continue

					while self.connected:
						try:
							msg = self.soc.recv(1024).decode()
							if msg.startswith("SCRIPT_GUI"):
								continue

							try:
								msg_obj = json.loads(msg)
								if msg_obj.get("type") == "robot utterance":
									utterance = msg_obj.get("utterance")
									dialog_state.robot_speech(utterance)
							except json.decoder.JSONDecodeError:
								print("JSON decode error, skipping message.")
								continue
						except Exception as e:
							print("Client error", e)
							traceback.print_exc()
							self.connected = False
							break
			except Exception as e:
				print("Critical error in connection loop:", e)
				traceback.print_exc()
			finally:
				if self.soc:
					try:
						self.soc.close()
					except Exception:
						pass
				self.connected = False
				print(f"Reconnecting in {RETRY_WAIT}s...")
				time.sleep(RETRY_WAIT)

	def send_message(self, message):
		if not self.connected:
			print("Not connected to ScriptBoard...")
			return
		try:
			self.soc.send((message + "\n").encode('utf-8'))
		except Exception as e:
			print(e)
			print("Server disconnected!")
			self.connected = False

class DialogState:

	def __init__(self, client):
		self.user_speaking = False
		self.turn_state = None
		self.silence_time_start = 0
		self.client = client
		self.silence_checked = False

		silenceThread = threading.Thread(target=self.check_for_silence)
		silenceThread.daemon = True
		silenceThread.start()
	
	def update_turn_state(self, t):
		if self.turn_state != t and not(self.turn_state == "ROBOT_TURN" and t == "HUMAN_TURN"):
			info = {}
			info["type"] = "turn"
			info["turn state"] = t
			if t == "HUMAN_TURN":
				self.user_speaking = True
				info["human id"] = 1
			self.turn_state = t
			self.client.send_message(json.dumps(info))
	
	def send_utterance_message(self, utterance):
		info = {}
		info["type"] = "asr"
		info["utterance"] = utterance
		info["human id"] = 1
		self.user_speaking = False
		self.silence_time_start = time.time()
		self.client.send_message(json.dumps(info))
	
	def robot_speech(self, utterance):
		self.update_turn_state("ROBOT_TURN")
		self.silence_time_start = time.time()
		print("Robot said:", utterance)
		self.GUI.show_robot_speech(utterance)
		time.sleep(1)
		info = {}
		info["type"] = "robot stop speech"
		info["utterance"] = utterance
		self.silence_time_start = time.time()
		self.client.send_message(json.dumps(info))
		self.update_turn_state("OFFER_TO_HUMAN")

	def update_speaking(self, s):
		self.user_speaking = s	

	def check_for_silence(self):
		while True:
			if self.turn_state == "HUMAN_TURN" and not self.user_speaking:
				if (time.time() - self.silence_time_start) >= 1.5:
					self.update_turn_state("OFFER_TO_ROBOT")
			if self.turn_state == "OFFER_TO_HUMAN":
				x = (time.time() - self.silence_time_start) * 1000
				info = {}
				info["type"] = "silence time"
				info["time"] = int(x)
				self.client.send_message(json.dumps(info))
			time.sleep(0.02)
			
	def quit_application(self):
		sys.exit()
	
	def setGUI(self, GUI):
		self.GUI = GUI


client = DialogManagerClient("localhost")
clientThread = threading.Thread(target=client.start_connecting)
clientThread.daemon = True
clientThread.start()

dialog_state = DialogState(client)

GUI = dmGUI.GUI(dialog_state)