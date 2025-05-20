import socket
import time
import json
import traceback

class Client:
	def __init__(self, host, port):
		# Server Address (port)
		self.HOST = host
		self.PORT = port
		self.soc = None
		self.connected = False
		self.response = ""
		self.streaming = False
		self.streamed_sentences = []

	def start_connecting(self):
		# Establishing a server
		self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		while not self.connected:
			try:
				self.soc.connect((self.HOST, self.PORT))
				print('Connected to LLM server', self.HOST, self.PORT)
				self.connected = True
			except ConnectionRefusedError as e:
				time.sleep(3)
				continue

		message = ""
		m = b''	

		while True:
			try:
				b = self.soc.recv(1024)
				try:
					m = m + b
					s = m.decode()
				except UnicodeDecodeError as e:
					continue

				m = b''
				message = message + s 

				try:
					message = json.loads(message)
				except json.decoder.JSONDecodeError as e:
					print("could not parse message", message)
					continue
			
				ended = message["ended"]
				response = message["sentence"]
				recv_type = message["type"]

				if recv_type == "unavailable":
					self.streaming = False
					message = ""
					m = b''
					self.response = None
					print("LLM response not available...")
					continue

				if recv_type == "stream" and ended == True:
					self.streaming = False
					message = ""
					m = b''
					continue
				
				response = response.replace("ROBOT:", "")

				message = ""
				m = b''

				if recv_type == "stream":
					self.streamed_sentences.append(response)
					print("LLM client sentences:", self.streamed_sentences)
				else:
					print(response)
					self.response = response

				if not self.connected:
					break
			except Exception as e:
				print("LLM client error", e)
				traceback.print_exc()
				self.connected = False
				self.soc.close()
				self.start_connecting()

	def send_message(self, message):
		if not self.connected:
			print("Not connected to server...")
			return
		try:
			self.soc.send((message + "\n").encode('utf-8'))
		except Exception as e:
			print(e)
			print("Server disconnected!")
			self.connected = False
