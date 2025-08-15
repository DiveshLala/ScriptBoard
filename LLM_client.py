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
		# Establishing a server with robust error handling
		RETRY_WAIT = 3
		MAX_JSON_FAIL = 10
		while True:
			try:
				self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.soc.settimeout(10)  # 10秒でタイムアウト
				while not self.connected:
					try:
						self.soc.connect((self.HOST, self.PORT))
						print('Connected to LLM server', self.HOST, self.PORT)
						self.connected = True
					except (ConnectionRefusedError, socket.timeout) as e:
						print(f"Connection failed: {e}. Retrying in {RETRY_WAIT}s...")
						time.sleep(RETRY_WAIT)
						continue

				message = ""
				m = b''
				json_fail_count = 0

				while self.connected:
					try:
						try:
							b = self.soc.recv(102400)
						except socket.timeout:
							continue  # タイムアウト時は再度recv
						if b == b'':
							print("Server closed connection.")
							self.connected = False
							break
						m = m + b
						try:
							s = m.decode()
						except UnicodeDecodeError:
							# 文字化け時は次の受信を待つ
							continue
						m = b''
						message += s

						try:
							msg_obj = json.loads(message)
							json_fail_count = 0  # 成功したらリセット
						except json.decoder.JSONDecodeError:
							json_fail_count += 1
							if json_fail_count > MAX_JSON_FAIL:
								print("Too many JSON decode failures. Resetting buffer.")
								message = ""
								json_fail_count = 0
							else:
								# 追加データを待つ
								continue

						ended = msg_obj.get("ended", False)
						response = msg_obj.get("sentence", "")
						recv_type = msg_obj.get("type", "")

						if recv_type == "unavailable":
							self.streaming = False
							message = ""
							m = b''
							self.response = None
							print("LLM response not available...")
							continue

						if recv_type == "stream" and ended:
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

					except Exception as e:
						print("LLM client error", e)
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
			print("Not connected to server...")
			return
		try:
			self.soc.send((message + "\n").encode('utf-8'))
		except Exception as e:
			print(e)
			print("Server disconnected!")
			self.connected = False
