import socket
import os
import time
import re
import time
import threading
import json
import traceback


try:
	from openai import OpenAI
	OPEN_AI_PACKAGE_AVAILABLE = True
except ImportError:
	print("Need to install Open AI packages to use GPT!")
	OPEN_AI_PACKAGE_AVAILABLE = False

try:
	from google import genai
	GOOGLE_GENAI_PACKAGE_AVAILABLE = True
except ImportError:
	GOOGLE_GENAI_PACKAGE_AVAILABLE = False
	print("Need to install Google packages to use Gemini!")



GPT_API_INFO = {}
GEMINI_API_INFO = {}

GPT_AVAILABLE = False
GEMINI_AVAILABLE = False

#class for sending message to server
class Server():

	def __init__(self, port):
		self.client_socket = None
		self.is_connected = False
		self.server_port = port
		self.input_utterance = ""
		self.turn = None
		self.send_lock = False
		self.server_type = "main LLM"

	def connect(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serversock.bind(('', self.server_port))
		serversock.listen(10)

		while True:
			print(self.server_type, 'module waiting for connection from server...')
			print('at port %d' % self.server_port)
			self.client_socket, client_address = serversock.accept()
			print('Client connected to', self.server_type, 'module')
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
	

	def process_message(self, message):
		print("processing", message)
		prompt = message["prompt"]
		recv_type = message['type']
		llm = message["llm"]
		print("Using", llm, recv_type)
		if llm == "gpt" and GPT_AVAILABLE:
			self.process_GPT_prompt(prompt, recv_type)
		elif llm == "gemini" and GEMINI_AVAILABLE:
			self.process_Gemini_prompt(prompt, recv_type)
		elif llm == "lmstudio":
			self.process_LMStudio_prompt(prompt, recv_type)
		else:
			message = json.dumps({"type": "unavailable", "sentence": "FAIL_RESPONSE", "ended": True})
			self.send_message(message)
		

	def process_GPT_prompt(self, prompt, recv_type):
		print("=======================================================")
		print("RECEIVE TYPE", recv_type)
		print(prompt)
		start_time = time.time()
		if recv_type == "block":
			response = send_GPT_request(prompt)
			# 失敗時はデフォルト応答
			if response == None:
				response = "FAIL_RESPONSE"
			print("Response time for", recv_type, ":", time.time() - start_time)
			print("Response", response, "\n")
			message = json.dumps({"type": "block", "sentence": response, "ended": True})

			#ensures that threads don't get merged
			while(self.send_lock):
				time.sleep(0.1)
			self.send_lock = True
			self.send_message(message)
			self.send_lock = False
        
		elif recv_type == "stream":
			response = send_GPT_request(prompt, server = self, recv_type="stream")

		print("==========================================================")

	
	def process_Gemini_prompt(self, prompt, recv_type):
		print("=======================================================")
		print("RECEIVE TYPE", recv_type)
		print(prompt)
		start_time = time.time()
		if recv_type == "block":
			response = send_Gemini_request(prompt)
			print(response)
			if response != None:
				print("Response time:", time.time() - start_time)
				print("Response", response, "\n")
				message = json.dumps({"type": "block", "sentence": response, "ended": True})

			#ensures that threads don't get merged
			while(self.send_lock):
				time.sleep(0.1)
			self.send_lock = True
			self.send_message(message)
			self.send_lock = False
		
		elif recv_type == "stream":
			response = send_Gemini_request(prompt, server = self, recv_type="stream")
		
		print("==========================================================")
	
	def process_LMStudio_prompt(self, prompt, recv_type):
		print("=======================================================")
		print("RECEIVE TYPE", recv_type)
		print(prompt)
		start_time = time.time()
		if recv_type == "block":
			response = send_LMStudio_request(prompt)
			print(response)
			if response != None:
				print("Response time for", recv_type, ":", time.time() - start_time)
				print("Response", response, "\n")
				message = json.dumps({"type": "block", "sentence": response, "ended": True})

			#ensures that threads don't get merged
			while(self.send_lock):
				time.sleep(0.1)
			self.send_lock = True
			self.send_message(message)
			self.send_lock = False
		
		elif recv_type == "stream":
			response = send_LMStudio_request(prompt, server = self, recv_type="stream")

		print("==========================================================")


# Fillers handles on a separate port
# At the moment only handles LMStudio models
class FillerServer(Server):

	def __init__(self, port):
		super().__init__(port)
		self.server_type = "filler"



def send_GPT_request(input_prompt, server = None, recv_type="block"):

	try:
		if GPT_API_INFO is None:
			return None

		login_key = GPT_API_INFO.get("key")
		model_version = GPT_API_INFO.get("model")

		if not login_key or not model_version:
			print("GPT login information incorrect!", login_key, model_version)
			return None

		if recv_type == "block":
			try:
				client = OpenAI(api_key=login_key)
				messages = [{"role" : "user", "content": input_prompt}]

				response = client.chat.completions.create(
					model=model_version,
					messages=messages
				)
				r = response.choices[0].message.content
				r = r.strip()
				r = re.sub(".*:", "", r)
				r = re.sub("応答文", "", r)
				r = re.sub(".*寄り添い.*。", "", r)
				r = re.sub(".*ふんわりキャラ.*。", "", r)
				try:
					token_total = response.usage.total_tokens
					print("%d tokens" % token_total)
				except Exception:
					print("no token data")
				if not r:
					return None
				return r
			except Exception as e:
				return None

		elif recv_type == "stream" and server is not None:
			try:
				client = OpenAI(api_key=login_key)
				messages = [{"role" : "user", "content": input_prompt}]
				response = client.chat.completions.create(messages=messages, model=model_version, stream=True)
			except Exception as e:
				send_failure_message_for_stream(server)
				return None

			sentence = ""
			sentence_markers = [".", "。", "?", "？", "!", "！"]
			for sse_chunk in response:
				content = sse_chunk.choices[0].delta.content
				if content is None:
					print("Finished stream...")
					message = json.dumps({"type": "stream", "sentence": "", "ended": True})
					server.send_message(message)
					break

				for token in content:
					sentence += token
					if token in sentence_markers:
						message = json.dumps({"type": "stream", "sentence": sentence, "ended": False})
						server.send_message(message)
						time.sleep(0.5)
						sentence = ""
			return None
		else:
			return None
	except Exception as e:
		print("Unexpected error in send_GPT_request:", e)
		if recv_type == "stream":
			send_failure_message_for_stream(server)
		return None

def send_Gemini_request(input_prompt, server= None, recv_type="block"):

	if GEMINI_API_INFO == None:
		return None

	login_key = GEMINI_API_INFO["key"]
	model_version = GEMINI_API_INFO["model"]

	if login_key == None or model_version == None:
		print("Gemini login information incorrect!", login_key, model_version)
		return None

	if recv_type == "block":
		try:
			client = genai.Client(api_key=login_key)
			response = client.models.generate_content(model=model_version, contents=input_prompt)
			if response == None:
				return None
			return response.text
		except Exception as e:
			print(e)
			return None
	elif recv_type == 'stream':
		try:
			client = genai.Client(api_key=login_key)
			sentence = ""
			sentence_markers = [".", "。", "?", "？", "!", "！"]
			for chunk in client.models.generate_content_stream(model=model_version, contents=input_prompt):
				for token in chunk.text:
					sentence += token
					if token in sentence_markers:
						message = json.dumps({"type": "stream", "sentence": sentence, "ended": False})
						server.send_message(message)
						time.sleep(0.1)
						sentence = ""

			message = json.dumps({"type": "stream", "sentence": "", "ended": True})
			server.send_message(message)
		except Exception as e:
			send_failure_message_for_stream(server)
			return None


def send_LMStudio_request(input_prompt, ip, port, server = None, recv_type="block"):
	lm_ip = "http://" + ip + ":" + str(port) + "/v1"
	client = OpenAI(
		base_url= lm_ip,
		api_key="lm-studio"  # Any string works
	)

	if recv_type == "block":
		try:
			response = client.chat.completions.create(
				model="your-model-id",
				messages=[
					{"role": "user", "content": input_prompt}
				]
			)
			r = response.choices[0].message.content
			return r
		except Exception as e:
			return None
	
	elif recv_type == 'stream':

		try:
			sentence = ""
			sentence_markers = [".", "。", "?", "？", "!", "！"]

			response = client.chat.completions.create(
				model="your-model-id",
				messages=[
					{"role": "user", "content": input_prompt}
				],
				stream = True
			)

			for chunk in response:

				if chunk.choices[0].delta.content == None:
					break

				for token in chunk.choices[0].delta.content:
					sentence += token
					if token in sentence_markers:
						
						sentence_ = sentence.strip()
						if len(sentence_) == 0:
							continue
						
						message = json.dumps({"type": "stream", "sentence": sentence_, "ended": False})
						server.send_message(message)
						time.sleep(0.1)
						sentence = ""

			message = json.dumps({"type": "stream", "sentence": "", "ended": True})
			server.send_message(message)
		except Exception as e:
			print(e)
			traceback.print_exc()
			send_failure_message_for_stream(server)
			return None

#return either None or a dictionary with the information 
def get_API_information(api_name, config_file):

	if api_name == "gpt":
		if not OPEN_AI_PACKAGE_AVAILABLE:
			return None
		
		try:
			f = open(config_file, "r").readlines()
		except FileNotFoundError:
			print("Missing API login information file!", config_file)
			return None

		api_key = None
		api_model = None

		for x in f:
			if len(x.strip()) == 0 or len(x.split("=")) <= 1:
				continue

			element = x.split("=")[0]
			value = x.split("=")[1].strip()

			if element == "GPT_KEY":
				api_key = value
			if element == "GPT_MODEL":
				api_model = value
		
		api_info = {"api": "gpt", "key": api_key, "model": api_model}

		return api_info

	elif api_name == "gemini":
		if not GOOGLE_GENAI_PACKAGE_AVAILABLE:
			return None
	
		try:
			f = open(config_file, "r").readlines()
		except FileNotFoundError:
			print("Missing API login information file!", config_file)
			return None

		api_key = None
		api_model = None

		for x in f:
			if len(x.strip()) == 0 or len(x.split("=")) <= 1:
				continue

			element = x.split("=")[0]
			value = x.split("=")[1].strip()

			if element == "GEMINI_KEY":
				api_key = value
			if element == "GEMINI_MODEL":
				api_model = value
		
		api_info = {"api": "gemini", "key": api_key, "model": api_model}

		return api_info

def check_for_GPT():
	global GPT_API_INFO
	global GPT_AVAILABLE
	global OPEN_AI_PACKAGE_AVAILABLE
	
	if not OPEN_AI_PACKAGE_AVAILABLE:
		return -1
	
	config_file = "./llm/llm_login_info.txt"

	if not os.path.exists(config_file):
		return -2
	
	GPT_API_INFO = get_API_information("gpt", config_file)

	if GPT_API_INFO["key"] == None or GPT_API_INFO["model"] == None:
		return -3
	
	response = send_GPT_request("Hello, what is your name?")

	if response == None:
		return -4

	GPT_AVAILABLE = True
	print("GPT AVAILABLE")
	return 0

def check_for_Gemini():
	global GEMINI_API_INFO
	global GEMINI_AVAILABLE
	global GOOGLE_GENAI_PACKAGE_AVAILABLE
	
	if not GOOGLE_GENAI_PACKAGE_AVAILABLE:
		return -1
	
	config_file = "./llm/llm_login_info.txt"

	if not os.path.exists(config_file):
		return -2
	
	GEMINI_API_INFO = get_API_information("gemini", config_file)

	if GEMINI_API_INFO["key"] == None or GEMINI_API_INFO["model"] == None:
		return -3

	response = send_Gemini_request("Hello, what is your name?")

	if response == None:
		return -4

	GEMINI_AVAILABLE = True
	print("GEMINI AVAILABLE")
	return 0

def check_for_LMStudio(ip, port):
	global OPEN_AI_PACKAGE_AVAILABLE

	if not OPEN_AI_PACKAGE_AVAILABLE:
		return -1
		
	response = send_LMStudio_request("Hello, what is your name?", ip, port)

	if response == None:
		return -5

	print("LM STUDIO model found")
	return 0

def send_failure_message_for_stream(server):
	message = json.dumps({"type": "stream", "sentence": "FAIL_RESPONSE", "ended": False})
	server.send_message(message)
	time.sleep(0.1)
	message = json.dumps({"type": "stream", "sentence": "", "ended": True})
	server.send_message(message)


server = Server(5042)
filler_server = FillerServer(6042)

t = threading.Thread(target=server.connect)
t.daemon = True
t.start()

t2 = threading.Thread(target=filler_server.connect)
t2.daemon = True
t2.start()

if __name__ == "__main__":
	while True:
		time.sleep(1)