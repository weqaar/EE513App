from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.switch import Switch
from kivy.uix.actionbar import ActionBar, ActionView, ActionItem, ActionPrevious, ActionButton, ActionOverflow, ActionGroup
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy import platform
import paho.mqtt.client as mqtt
from plyer import vibrator, accelerometer
import threading
import time
import queue
import hashlib

#setup graphics
from kivy.config import Config
Config.set('graphics','resizable',0)
 
#Graphics fix
from kivy.core.window import Window;
Window.clearcolor = (0,0,0,1.)

class MainScreen(GridLayout):

	_data_object = { "server": None,
					 "port": None,
					 "protocol": None,
					 "topic_url": None,
					 "platform": str(platform)
			   }
		
	def __init__(self, **kwargs):
		super(MainScreen, self).__init__(**kwargs)
	
		self.cols = 1
		self.rows = 1

		self._data_queue = queue.Queue()

		#Layouts
		self._main_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 1))
		_terminal_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 0.7))
		_partition_layout = GridLayout(cols=2, rows=5, padding=0, size_hint=(1, 1), row_force_default=True, \
									   rows_minimum={0: 150, 1: 150, 2: 150, 3: 150}, row_default_height=150, spacing=25)
  
		_action_previous = ActionPrevious(title='EE513 LABS', with_previous=False, app_icon='icons/chip.png', padding=0)
		_action_overflow = ActionOverflow()
		_action_view = ActionView(overflow_group=_action_overflow, use_separator=True)
		_action_button = ActionButton(text='config')
		_action_overflow.add_widget(_action_button)
		_action_button_about = ActionButton(text='About')
		_action_button_about.bind(on_release=self._popup_about)
		_action_view.add_widget(_action_previous)
		_action_view.add_widget(_action_button_about)
		_action_view.add_widget(_action_overflow)
		_action_bar = ActionBar(pos_hint={'top': 1})
		_action_bar.add_widget(_action_view)

		_partition_layout.add_widget(Label(text='Server', size_hint_x=None, width=400))
	
		self.server = TextInput(text='192.168.0.20', multiline=False, cursor_blink=True)
		self.server.bind(text=self.callback_server_text)
		_partition_layout.add_widget(self.server)
	
		_partition_layout.add_widget(Label(text='Port', size_hint_x=None, width=400))
	
		self.port = TextInput(text='1883', multiline=False)
		self.port.bind(text=self.callback_port_text)
		_partition_layout.add_widget(self.port)

		_partition_layout.add_widget(Label(text='Protocol', size_hint_x=None, width=400))

		spinner = Spinner(
					text='mqtt',
					values=('http', 'mqtt'),
					size_hint=(0.3, 0.5), sync_height=True)

		spinner.bind(text=self.callback_spinner_text)
		_partition_layout.add_widget(spinner)

		_partition_layout.add_widget(Label(text='Topic/URL', size_hint_x=None, width=400))
		self.topic_url = TextInput(text='/ie/dcu/ee513', multiline=False)
		self.topic_url.bind(text=self.callback_topic_url_text)
		_partition_layout.add_widget(self.topic_url)
  
		_partition_layout.add_widget(Label(text='Connect', size_hint_x=None, width=400))
		switch = Switch()
		switch.bind(active=self.callback_switch)
		_partition_layout.add_widget(switch)

		self.terminal = TextInput(text='Terminal output...', multiline=True, readonly=False, size_hint=(1, 1))
		self.global_terminal = self.terminal
		_terminal_layout.add_widget(self.terminal)		
		
		self._main_layout.add_widget(_action_bar)
		self._main_layout.add_widget(_partition_layout)
		self._main_layout.add_widget(_terminal_layout)
		self.add_widget(self._main_layout)

	def callback_switch(self, instance, value):
		if (value is True):
			terminal_thread = threading.Thread(target=self.publish_terminal, args=(self.global_terminal, self._data_queue, ))
			terminal_thread.start()
			try:
				load_jnius_nih()
			except Exception as _exp:
				self.global_terminal.insert_text("Exception: " + str(_exp) + "\n")
		elif (value is False):
			self._data_queue.put("exit")
   
	def on_pause(self):
		return True

	def _popup_about(self, event):
		popup_text = "Author: WEQAAR JANJUA, EE513\n\nweqaar.janjua2@mail.dcu.ie\n\n" + \
					"DCU Electronic and Computer Engineering\n\n" + \
					"http://www.dcu.ie"
		popup_box = BoxLayout(orientation = 'vertical', padding = 0)
		_content = Label(text = popup_text, halign='center', valign='middle')
		popup_box.add_widget(_content)
		close_button = Button(text='close', size_hint=(0.2, 0.1), pos_hint={'center_x': .5, 'center_y': .5})
		popup_box.add_widget(close_button)
		__popup = Popup(title='Accelerometer Data Transmitter', title_align = 'center', \
						content = popup_box, size_hint=(1, 1), auto_dismiss=False)
		close_button.bind(on_press=__popup.dismiss)
		__popup.open()


	def _popup_debug(self, event):
		popup_box = BoxLayout(orientation = 'vertical', padding = 0)
		_content = Label(text = str(self._data_object), halign='center', valign='middle')
		popup_box.add_widget(_content)
		close_button = Button(text='close', size_hint=(0.2, 0.1), pos_hint={'center_x': .5, 'center_y': .5})
		popup_box.add_widget(close_button)
		__popup = Popup(title='Debug', title_align = 'center', \
						content = popup_box, size_hint=(1, 1), auto_dismiss=False)

		close_button.bind(on_press=__popup.dismiss)
		__popup.open()

	def callback_server_text(self, instance, value):
		self._data_object["server"] = str(value)

	def callback_port_text(self, instance, value):
		self._data_object["port"] = str(value)

	def callback_spinner_text(self, spinner, text):
		self._data_object["protocol"] = text

	def callback_topic_url_text(self, instance, value):
		self._data_object["topic_url"] = value

	def publish_terminal(self, terminal, _data_queue):
		terminal.insert_text("\n")
		if (platform == 'android') or (platform == 'ios'):
			vibrator.vibrate(1)
			try:
				accelerometer.enable()
			except Exception as _exp:
				terminal.insert_text("Exception: " + str(_exp) + "\n")
		previous_payload_hash = None	
		while True:
			if _data_queue.empty() is False:
				qdata = _data_queue.get()
				if qdata == "exit":
					break
			if (platform == 'android') or (platform == 'ios'):
				if None in accelerometer.acceleration:
					pass
				else:
					payload_hash = hashlib.md5(str(accelerometer.acceleration).encode('utf-8')).hexdigest()
					if (previous_payload_hash is not None):
						if (previous_payload_hash == payload_hash):
							pass
						else:
							previous_payload_hash = payload_hash
							terminal.insert_text("AXL (x, y, z): " + str(accelerometer.acceleration) + "\n")
							time.sleep(0.1)
					else:
						terminal.insert_text("AXL (x, y, z): " + str(accelerometer.acceleration) + "\n")
						time.sleep(0.1)
			else:
				terminal.insert_text("time: " + str(time.strftime("%c", time.gmtime())) + "\n")
				time.sleep(2)

#Bug fix, src: https://github.com/jeremyklelifa/Jukebar/commit/0607c7cb4dcef2125ab1b2b70227a7999f7caabe
#Another potential solution: https://github.com/VoiceThread/pyjnius
def load_jnius_nih():
	"""
	Creates org.jnius.NativeInvocationHandler once in the main thread
	to wordaround the error:
	JavaException: Class not found 'org/jnius/NativeInvocationHandler'
	see:
	  - https://github.com/kivy/pyjnius/issues/137
	  - https://github.com/kivy/pyjnius/issues/223
	  - http://stackoverflow.com/a/27943091/185510
	"""
	from jnius import autoclass
	autoclass('org.jnius.NativeInvocationHandler')
	
class AXLApp(App):

	def build(self):
		return MainScreen()
		
		
if __name__ == "__main__":
	AXLApp().run()
