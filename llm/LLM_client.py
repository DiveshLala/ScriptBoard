import socket
import time
import json
import traceback

# A default client will be created for the LLM API serer
# This same class can be reused for custom LLM models
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
		self.client_type = "main LLM"
		self.is_removed = False

	def start_connecting(self):
		# Establishing a server with robust error handling
		RETRY_WAIT = 3
		while True:
			if self.is_removed:
				break
			try:
				self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.soc.settimeout(10)  # 10秒でタイムアウト
				while not self.connected:
					if self.is_removed:
						break
					try:
						self.soc.connect((self.HOST, self.PORT))
						print('Connected to', self.client_type,  'server', self.HOST, self.PORT)
						self.connected = True
					except (ConnectionRefusedError, socket.timeout) as e:
						print(f"Connection failed: {e}. Retrying in {RETRY_WAIT}s...")
						time.sleep(RETRY_WAIT)
						continue

					while self.connected:
						if self.is_removed:
							break
						try:
							# まず4バイトで長さを受信
							total_data = b''
							while len(total_data) < 4:
								try:
									chunk = self.soc.recv(4 - len(total_data))
								except socket.timeout:
									continue
								if chunk == b'':
									print("Server closed connection.")
									self.connected = False
									break
								total_data += chunk
							if not self.connected:
								break
							msg_len = int.from_bytes(total_data, byteorder='big')
							# 本体を受信
							data = b''
							while len(data) < msg_len:
								try:
									chunk = self.soc.recv(msg_len - len(data))
								except socket.timeout:
									continue
								if chunk == b'':
									print("Server closed connection.")
									self.connected = False
									break
								data += chunk
							if not self.connected:
								break
							print('<RECEIVED MESSAGE>')
							try:
								message = data.decode()
								print("Received message:", message)
							except UnicodeDecodeError:
								print("Decode error, skipping message.")
								self.streaming = False
								self.response = None
								break
							try:
								msg_obj = json.loads(message)
							except json.decoder.JSONDecodeError:
								print("JSON decode error, skipping message.")
								self.streaming = False
								self.response = None
								break
							ended = msg_obj.get("ended", False)
							response = msg_obj.get("sentence", "")
							recv_type = msg_obj.get("type", "")
							if recv_type == "unavailable":
								self.streaming = False
								self.streamed_sentences.append("FAIL_RESPONSE")
								self.response = response
								print("LLM response not available...")
								continue
							
							print("LLM response:", response)
							print('ended:', ended)
							print('recv_type:', recv_type)

							if recv_type == "stream" and ended:
								self.streaming = False
								continue
							response = response.replace("ROBOT:", "")
							response = response.replace("HUMAN:", "")
							if recv_type == "stream":
								self.streamed_sentences.append(response)
								print("LLM client sentences:", self.streamed_sentences)
							else:
								print(response)
								self.response = response
						except Exception as e:
							print("LLM client error", e)
							traceback.print_exc()
							self.connected = False
							break
					print("Client has been removed...")
			except Exception as e:
				print("Critical error in connection loop:", e)
				traceback.print_exc()
			finally:
				if not self.is_removed:
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
			print("Not connected to server...")
			return
		try:
			self.soc.send((message + "\n").encode('utf-8'))
		except Exception as e:
			print(e)
			print("Server disconnected!")
			self.connected = False

#use a separate port to receive fillers
class FillerClient(Client):
	def __init__(self, host, port):
		super().__init__(host, port)
		self.client_type = "filler"

class CustomLLMClient(Client):
	def __init__(self, host, port):
		super().__init__(host, port)
		self.client_type = "custom_model"
	
	def shutdown(self):
		self.is_removed = True

