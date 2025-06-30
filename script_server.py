import socket
import traceback
import json

class Server:
	def __init__(self, port):
		# Server Address (port)
		self.PORT = port
		self.soc = None
		self.processor = None
		self.connected = False

	def set_processor(self, p):
		self.processor = p
	
	def set_main_window(self, m):
		self.main_window = m

	def start_connecting(self):
		# Establishing a server
		self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		hostname = socket.gethostname()
		ip_address = socket.gethostbyname(hostname)
		self.soc.bind((hostname, self.PORT))
		self.soc.listen()
		print('Waiting for connection on ', ip_address, self.PORT)

		try:
			while True:
				self.client_soc, client_addr = self.soc.accept() # Keep running this loop
				print('Connected at ', client_addr)
				self.connected = True
				self.main_window.updateServerConnectionStatus(self.connected)
				#send the name of this script
				self.send_message("SCRIPT_GUI:Connected")

				part_bytes = b''
				part_message = ""

				while True:

					try:
						m = self.client_soc.recv(1024)
						m = part_bytes + m
						message = m.decode()
						part_bytes = b''
					except UnicodeDecodeError as e:
						part_bytes = m
						continue
					except socket.error:
						print("Socket disconnected...")
						self.soc.close()
						self.connected = False
						self.main_window.updateServerConnectionStatus(self.connected)
						self.start_connecting()
						break

					# check if message is a valid JSON string
					try:
						message = part_message + message
						x = message.split("\n")
						for msg in x:
							if len(msg.strip()) == 0:
								continue
							json_msg = json.loads(msg)
							if self.processor != None:
								self.processor.message_notification(json_msg)
							message = message.replace(msg, "")
						part_message = message
						if len(part_message.strip()) == 0:
							part_message = ''
					except json.JSONDecodeError as e:
						part_message = message
						print("incorrect message..", part_message)
						continue

		except Exception as e:
			print(traceback.format_exc())
			self.connected = False
			print('Disconnected, waiting...')
	
	def send_message(self, message):
		if not self.connected:
			print("Server not connected...")
			return
		
		try:
			self.client_soc.send((message + "\n").encode('utf-8'))
		except Exception as e:
			print(e)
			print("Client disconnected!")