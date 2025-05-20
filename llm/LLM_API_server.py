import socket
import os
import time
import re
import time
import threading
import json


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

	def connect(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		serversock.bind(('', self.server_port))
		serversock.listen(10)

		while True:
			print('LLM module waiting for connection from server...')
			print('at port %d' % self.server_port)
			self.client_socket, client_address = serversock.accept()
			print('client connected to LLM module')
			self.is_connected = True
			
			part_message = ''
			part_bytes = b''

			while self.is_connected:
				while True:
					try:
						recvmessage = self.client_socket.recv(4096)
						m = part_bytes + recvmessage
						message = m.decode(encoding="utf-8")
						part_bytes = b''
					except UnicodeDecodeError as e:
						part_bytes = m
						continue
					except socket.error:
						print ('Error receiving data from server')
						self.is_connected = False
						break

					try:
						message = part_message + message
						json_msg = json.loads(message)
						self.process_message(json_msg)
						part_message = ''
					except json.JSONDecodeError as e:
						part_message = message
						print("incorrect message..", part_message)
						continue

			print("Reconnecting...")

	def send_message(self, message):
		try:
			chunks = [message[i:i+200] for i in range(0, len(message), 200)]
			for m in chunks:
				self.client_socket.send(m.encode())
		except:
			print("Server disconnected!")
			self.is_connected = False
	

	def process_message(self, message):
		print("processing", message)
		prompt = message["prompt"]
		recv_type = message['type']
		llm = message["llm"]
		print("Using", llm, recv_type, GPT_AVAILABLE)
		if llm == "gpt" and GPT_AVAILABLE:
			self.process_GPT_prompt(prompt, recv_type)
		elif llm == "gemini" and GEMINI_AVAILABLE:
			self.process_Gemini_prompt(prompt, recv_type)
		else:
			message = json.dumps({"type": "unavailable", "sentence": "", "ended": True})
			self.send_message(message)
		
	def process_GPT_prompt(self, prompt, recv_type):
		print("=======================================================")
		print("RECEIVE TYPE", recv_type)
		print(prompt)
		start_time = time.time()
		if recv_type == "block":
			response = send_GPT_request(prompt)
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

def send_GPT_request(input_prompt, server = None, recv_type="block"):

	if GPT_API_INFO == None:
		return None

	login_key = GPT_API_INFO["key"]
	model_version = GPT_API_INFO["model"]

	if login_key == None or model_version == None:
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
			r.strip()
			r = re.sub(".*:", "", r)
			r = re.sub("応答文", "", r)
			r = re.sub(".*寄り添い.*。", "", r)
			r = re.sub(".*ふんわりキャラ.*。", "", r)
			try:
				token_total = response.usage.total_tokens
				print("%d tokens" % token_total)
			except:
				print("no token data")
			return r

		except Exception as e:
			print(e)
			return None

	elif recv_type == "stream" and server != None:
		client = OpenAI(api_key=login_key)

		messages = [{"role" : "user", "content": input_prompt}]

		try:
			response = client.chat.completions.create(messages=messages, model=model_version, stream=True)
		except Exception as e:
			print(e)
			return None

		sentence = ""
		sentence_markers = [".", "。", "?", "？", "!", "！"]
		for sse_chunk in response:
			content = sse_chunk.choices[0].delta.content
			if content == None:
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

def send_Gemini_request(input_prompt, server= None, recv_type="block"):

	if GEMINI_API_INFO == None:
		return None

	login_key = GEMINI_API_INFO["key"]
	model_version = GEMINI_API_INFO["model"]

	if login_key == None or model_version == None:
		print("Gemini login information incorrect!", login_key, model_version)
		return None

	print("RECV TYPE", recv_type)
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
						print("message", message)
						server.send_message(message)
						time.sleep(0.1)
						sentence = ""

			message = json.dumps({"type": "stream", "sentence": "", "ended": True})
			server.send_message(message)
		except Exception as e:
			print(e)
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
			if len(x.strip()) == 0:
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
			if len(x.strip()) == 0:
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

	response = send_GPT_request("Hello, what is your name?", "gpt")

	if response == None:
		return -4

	GPT_AVAILABLE = True
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

	response = send_Gemini_request("Hello, what is your name?", "gemini")

	if response == None:
		return -4

	GEMINI_AVAILABLE = True
	return 0

server = Server(5042)

t = threading.Thread(target=server.connect)
t.daemon = True
t.start()

if __name__ == "__main__":
	while True:
		time.sleep(1)