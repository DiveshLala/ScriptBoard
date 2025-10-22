import socket
import json

#class for sending message to server
class Server():

	def __init__(self, port):
		self.client_socket = None
		self.is_connected = False
		self.server_port = port

	def listen(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serversock.bind(('', self.server_port))
		serversock.listen(10)

		while True:
			print("Custom LLM server waiting on port", self.server_port)
			self.client_socket, client_address = serversock.accept()
			print('Client connected to Custom LLM')
			self.is_connected = True

			buffer = ""

			while self.is_connected:
				try:
					recvmessage = self.client_socket.recv(409600)
					if not recvmessage:
						print("Client disconnected.")
						self.is_connected = False
						break
					buffer += recvmessage.decode("utf-8")
					while "\n" in buffer:
						line, buffer = buffer.split("\n", 1)
						if not line.strip():
							print("Empty line received, skipping...")
							continue
						try:
							json_msg = json.loads(line)
							self.process_message(json_msg)
						except json.JSONDecodeError:
							print("incorrect message..", line)
							continue
				except UnicodeDecodeError as e:
					print("Unicode decode error:", e)
					continue
				except socket.error:
					print('Error receiving data from server')
					self.is_connected = False
					break
				except Exception as e:
					print("Unexpected error:", e)
					self.is_connected = False
					break

			print("Reconnecting...")

	def send_message(self, message):
			try:
				# メッセージをエンコード
				data = message.encode()
				# 長さを4バイトbig endianで送信
				length = len(data)
				self.client_socket.send(length.to_bytes(4, byteorder='big'))
				# 本体を送信
				self.client_socket.send(data)
			except:
				print("Server disconnected!")
				self.is_connected = False

server = Server(1555)
server.listen()