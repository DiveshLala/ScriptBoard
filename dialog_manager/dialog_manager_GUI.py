from tkinter import Tk, Frame, BOTH, Label, Button, Text, Checkbutton, BooleanVar, END
import datetime

class GUI(Frame):
	def __init__(self, controller):
		self.root = Tk()
		self.root.geometry("530x200+300+300")
		self.dialog_controller = controller
		self.dialog_controller.setGUI(self)
		self.GUI = self.load_GUI(self.root)
		self.log_conversation = False
		self.log_file = None
		self.root.wm_protocol("WM_DELETE_WINDOW", self.quit_GUI)
		self.root.mainloop()
		self.root.quit()
	

	def quit_GUI(self):
		if self.log_conversation and self.log_file != None:
			self.log_file.close()
		self.GUI = None
		self.root.destroy()
		self.dialog_controller.quit_application()
	

	def load_GUI(self, root):
		Frame.__init__(self, root)
		self.parent = root
		self.isLoaded = False
		self.init_UI()
	
	def init_UI(self):
		self.parent.title("Lightweight Dialog Manager for ScriptBoard")
		self.pack(fill=BOTH, expand=1)

		self.make_ASR_input()
		self.robot_response_display()
		self.log_check()

		self.isLoaded = True
	

	def make_ASR_input(self):
		Label(text = "Simulated ASR", font=('Arial', 12, 'bold')).place(x = 30, y = 30)
		self.input_utterance = Text(self.root, height = 1,width = 30, wrap=None)
		self.input_utterance.bind("<KeyRelease>", lambda e: self.update_turn_state("HUMAN_TURN"))
		self.input_utterance.place(x = 30, y = 50)

		self.confirm_utterance = Button(self.root, text="Send utterance")
		self.confirm_utterance.bind("<Button-1>", lambda e: self.finish_utterance(self.input_utterance.get('1.0', 'end-1c')))
		self.confirm_utterance.place(x = 300, y = 45)
	
	def robot_response_display(self):
		self.robot_speech = Label(self.root, text="", wraplength=400, justify="left", font=("Arial", 12)) 
		self.robot_speech.place(x = 30, y = 80)
	
	def log_check(self):
		self.log_var = BooleanVar()
		self.log_var.set(False)
		self.log_check = Checkbutton(self.root, text="Log conversation (new file will be created)", font=("Arial", 10), variable=self.log_var, command=self.set_log) 
		self.log_check.place(x = 30, y = 120)
	
	def set_log(self):
		self.log_conversation = self.log_var.get()
		if self.log_conversation:
			dt_now = datetime.datetime.now()
			start_time_str = dt_now.strftime('%Y%m%d%H%M%S')
			self.log_file = open(start_time_str + ".txt", "a", encoding="utf-8")
		elif self.log_file != None:
			self.log_file.close()
			self.log_file = None
	
	def show_robot_speech(self, text):
		self.robot_speech.config(text=text)
		if self.log_conversation:
			self.log_file.write("ROBOT: " + text + "\n")
	
	def update_turn_state(self, turn_state):
		num_char = len(self.input_utterance.get('1.0', 'end-1c'))
		if num_char > 0:
			self.dialog_controller.update_turn_state(turn_state)
	
	def finish_utterance(self, utterance):
		if len(utterance) > 0:
			self.input_utterance.delete('1.0', END)
			self.dialog_controller.send_utterance_message(utterance)
			if self.log_conversation:
				self.log_file.write("HUMAN: " + utterance + "\n")