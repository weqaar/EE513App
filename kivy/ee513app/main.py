"""
Sensor Data Transmitter
Transmits over MQTT, HTTP, HTTPS, UDP

Author: Weqaar Janjua, <weqaar.janjua2@mail.dcu.ie>
		EE513, DCU Electronic and Computer Engineering
"""
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
from plyer import vibrator, accelerometer, compass, gps, barometer, gravity, gyroscope
import threading
import time
import queue
import hashlib
import requests
import socket

#setup graphics
from kivy.config import Config
Config.set('graphics','resizable',0)
 
#Graphics fix
from kivy.core.window import Window
Window.clearcolor = (0,0,0,1.)

class MainScreen(GridLayout):

	_data_object = { "server": None,
					 "port": None,
					 "protocol": None,
					 "topic_url": None,
					 "sensor": None,				 
					 "platform": str(platform)
				}
		
	def __init__(self, **kwargs):
		super(MainScreen, self).__init__(**kwargs)
	
		self.cols = 1
		self.rows = 1

		self._data_queue = queue.Queue()
		self.gps_location = None
		self.gps_status = None
		self.default_sensor = "Accelerometer"
		self.default_protocol = "terminal"
		self.default_server = "test.mosquitto.org"
		self.default_port = "1883"
		self.default_topic_url = "ie/dcu/ee513"

		#Layouts
		self._main_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 1))
		if (platform == 'android') or (platform == 'ios'):
			_terminal_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 0.7))
			_partition_layout = GridLayout(cols=2, rows=6, padding=0, size_hint=(1, 1), row_force_default=True, \
										rows_minimum={0: 150, 1: 150, 2: 150, 3: 150}, row_default_height=150, spacing=25)
		else:
			_terminal_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 0.4))
			_partition_layout = GridLayout(cols=2, rows=6, padding=0, size_hint=(1, 1), row_force_default=True, \
										rows_minimum={0: 50, 1: 50, 2: 50, 3: 50}, row_default_height=50, spacing=25)
  
		_action_previous = ActionPrevious(title='EE513 LABS', with_previous=False, app_icon='icons/chip.png', padding=0)
		_action_overflow = ActionOverflow()
		_action_view = ActionView(overflow_group=_action_overflow, use_separator=True)
		_action_button = ActionButton(text='debug')
		_action_overflow.add_widget(_action_button)
		_action_button_about = ActionButton(text='About')
		_action_button_about.bind(on_release=self._popup_about)
		_action_button_quit = ActionButton(text='Quit')
		_action_button_quit.bind(on_release=self.quitApp)
		_action_view.add_widget(_action_previous)
		_action_view.add_widget(_action_button_about)
		_action_view.add_widget(_action_button_quit)
		_action_view.add_widget(_action_overflow)
		_action_bar = ActionBar(pos_hint={'top': 1})
		_action_bar.add_widget(_action_view)

		_partition_layout.add_widget(Label(text='Server', size_hint_x=None, width=400))
		self._data_object["server"] = self.default_server
		self.server = TextInput(text='test.mosquitto.org', multiline=False, cursor_blink=True)
		self.server.bind(text=self.callback_server_text)
		_partition_layout.add_widget(self.server)
	
		_partition_layout.add_widget(Label(text='Port', size_hint_x=None, width=400))
		self._data_object["port"] = self.default_port
		self.port = TextInput(text='1883', multiline=False)
		self.port.bind(text=self.callback_port_text)
		_partition_layout.add_widget(self.port)

		_partition_layout.add_widget(Label(text='Sensor', size_hint_x=None, width=400))
		self._data_object["sensor"] = self.default_sensor
		sensor_spinner = Spinner(
					text=self.default_sensor,
					values=('Accelerometer', 'Compass', 'GPS', 'Barometer', 'Gravity', 'Gyroscope'),
					size_hint=(0.3, 0.5), sync_height=True)
		sensor_spinner.bind(text=self.callback_sensor_spinner_text)
		_partition_layout.add_widget(sensor_spinner)

		_partition_layout.add_widget(Label(text='Protocol', size_hint_x=None, width=400))
		self._data_object["protocol"] = self.default_protocol
		protocol_spinner = Spinner(
					text=self.default_protocol,
					values=('http', 'https', 'mqtt', 'udp', 'terminal'),
					size_hint=(0.3, 0.5), sync_height=True)
		protocol_spinner.bind(text=self.callback_protocol_spinner_text)
		_partition_layout.add_widget(protocol_spinner)

		_partition_layout.add_widget(Label(text='Topic/URL', size_hint_x=None, width=400))
		self._data_object["topic_url"] = self.default_topic_url
		self.topic_url = TextInput(text='ie/dcu/ee513', multiline=False)
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
			if (platform == 'android') or (platform == 'ios'):
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
		__popup = Popup(title='Sensor Data Transmitter', title_align = 'center', \
						content = popup_box, size_hint=(1, 1), auto_dismiss=False)
		close_button.bind(on_press=__popup.dismiss)
		__popup.open()

	def quitApp(self, event):
		App.get_running_app().stop()

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

	def callback_protocol_spinner_text(self, spinner, text):
		self._data_object["protocol"] = text

	def callback_sensor_spinner_text(self, spinner, text):
		self._data_object["sensor"] = text

	def callback_topic_url_text(self, instance, value):
		self._data_object["topic_url"] = value

	"""
	src: https://github.com/kivy/plyer/blob/master/examples/gps/main.py
	"""
	def on_location(self, **kwargs):
		self.gps_location = '\n'.join(['{}={}'.format(k, v) for k, v in kwargs.items()])
	
	"""
	src: https://github.com/kivy/plyer/blob/master/examples/gps/main.py
	"""
	def on_status(self, stype, status):
		self.gps_status = 'type={}\n{}'.format(stype, status)
 	
	def xmit_payload(self, payload):
		if (self._data_object.get("protocol") == "mqtt"):
			try:
				mqttc = mqtt.Client()
				mqttc.connect(self._data_object.get("server"), port=int(self._data_object.get("port")), keepalive=5)
				_ret = mqttc.publish(self._data_object.get("topic_url"), payload)
				ret_status = _ret.rc
				mqttc.disconnect()
			except Exception as _exp:
				ret_status = _exp
			return str(ret_status)
		elif (self._data_object.get("protocol") == "http"):
			http_payload = { 'payload': payload }
			try:
				ret_status = requests.post("http://" + self._data_object.get("server") + \
   										   ":" + self._data_object.get("port") + "/" + \
                    					   self._data_object.get("topic_url").strip("/"), data=http_payload) 
			except Exception as _exp:
				ret_status = _exp
			return str(ret_status)
		elif (self._data_object.get("protocol") == "https"):
			https_payload = { 'payload': payload }
			try:
				ret_status = requests.post("https://" + self._data_object.get("server") + \
   										   ":" + self._data_object.get("port") + "/" + \
                    					   self._data_object.get("topic_url").strip("/"), data=https_payload) 
			except Exception as _exp:
				ret_status = _exp
			return str(ret_status)
		elif (self._data_object.get("protocol") == "udp"):
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				byte_payload = bytes(payload, "utf-8")
				sock.sendto(byte_payload, (self._data_object.get("server"), int(self._data_object.get("port"))))
				ret_status = "sent"
			except Exception as _exp:
				ret_status = _exp
			return str(ret_status)
		else:
			return str(False)

   
	def publish_terminal(self, terminal, _data_queue):
		terminal.insert_text("\n")
  
		if (platform == 'android') or (platform == 'ios'):
			try:
				vibrator.vibrate(1)
			except:
				pass

			#Accelerometer
			if self._data_object.get("sensor") == "Accelerometer":
				try:
					accelerometer.enable()
				except Exception as _exp:
					terminal.insert_text("Exception: " + str(_exp) + "\n")
					return
				previous_payload_hash = None	
				while True:
					if _data_queue.empty() is False:
						qdata = _data_queue.get()
						if qdata == "exit":
							try:
								accelerometer.disable()
							except:
								pass
							break
					if None in accelerometer.acceleration:
						pass
					else:
						payload_hash = hashlib.md5(str(accelerometer.acceleration).encode('utf-8')).hexdigest()
						if (previous_payload_hash is not None):
							if (previous_payload_hash == payload_hash):
								pass
							else:
								previous_payload_hash = payload_hash
								payload = "(x, y, z): " + str(accelerometer.acceleration)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
								time.sleep(0.1)
						else:
							payload = "(x, y, z): " + str(accelerometer.acceleration)
							terminal.insert_text(payload + "\n")
							if (self._data_object.get("protocol") != "terminal"):
								try:
									terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
								except Exception as _exp:
									terminal.insert_text("Exception: " + str(_exp) + "\n")
									return
							time.sleep(0.1)
			#Compass
			elif self._data_object.get("sensor") == "Compass":
				try:
					compass.enable()
				except Exception as _exp:
					terminal.insert_text("Exception: " + str(_exp) + "\n")
					return
				previous_payload_hash = None	
				while True:
					if _data_queue.empty() is False:
						qdata = _data_queue.get()
						if qdata == "exit":
							try:
								compass.disable()
							except:
								pass
							break
					if None in compass.field:
						pass
					else:
						payload_hash = hashlib.md5(str(compass.field).encode('utf-8')).hexdigest()
						if (previous_payload_hash is not None):
							if (previous_payload_hash == payload_hash):
								pass
							else:
								previous_payload_hash = payload_hash
								payload = "(x, y, z): " + str(compass.field)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
								time.sleep(0.1)
						else:
							payload = "(x, y, z): " + str(compass.field)
							terminal.insert_text(payload + "\n")
							if (self._data_object.get("protocol") != "terminal"):
								try:
									terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
								except Exception as _exp:
									terminal.insert_text("Exception: " + str(_exp) + "\n")
									return
							time.sleep(0.1)
			#GPS
			elif self._data_object.get("sensor") == "GPS":
				try:
					gps.configure(on_location=self.on_location, on_status=self.on_status)
					gps.start(1000, 0)
				except Exception as _exp:
					terminal.insert_text("Exception: " + str(_exp) + "\n")
					return
				previous_payload_hash = None	
				while True:
					if _data_queue.empty() is False:
						qdata = _data_queue.get()
						if qdata == "exit":
							try:
								gps.stop()
							except:
								pass
							break
					if self.gps_location is None:
						pass
					else:
						payload_hash = hashlib.md5(str(self.gps_location).encode('utf-8')).hexdigest()
						if (previous_payload_hash is not None):
							if (previous_payload_hash == payload_hash):
								pass
							else:
								previous_payload_hash = payload_hash
								payload = str(self.gps_location)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
								time.sleep(3)
						else:
							payload = str(self.gps_location)
							terminal.insert_text(payload + "\n")
							if (self._data_object.get("protocol") != "terminal"):
								try:
									terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
								except Exception as _exp:
									terminal.insert_text("Exception: " + str(_exp) + "\n")
									return
							time.sleep(0.5)
			#Barometer
			elif self._data_object.get("sensor") == "Barometer":
				try:
					barometer.enable()
				except Exception as _exp:
					terminal.insert_text("Exception: " + str(_exp) + "\n")
					return
				previous_payload_hash = None	
				while True:
					if _data_queue.empty() is False:
						qdata = _data_queue.get()
						if qdata == "exit":
							try:
								barometer.disable()
							except:
								pass
							break
					if barometer.pressure is None:
						pass
					else:
						payload_hash = hashlib.md5(str(barometer.pressure).encode('utf-8')).hexdigest()
						if (previous_payload_hash is not None):
							if (previous_payload_hash == payload_hash):
								pass
							else:
								previous_payload_hash = payload_hash
								payload = "hPa: " + str(barometer.pressure)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
								time.sleep(0.1)
						else:
							payload = "hPa: " + str(barometer.pressure)
							terminal.insert_text(payload + "\n")
							if (self._data_object.get("protocol") != "terminal"):
								try:
									terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
								except Exception as _exp:
									terminal.insert_text("Exception: " + str(_exp) + "\n")
									return
			#Gravity
			elif self._data_object.get("sensor") == "Gravity":
				try:
					gravity.enable()
				except Exception as _exp:
					terminal.insert_text("Exception: " + str(_exp) + "\n")
					return
				previous_payload_hash = None	
				while True:
					if _data_queue.empty() is False:
						qdata = _data_queue.get()
						if qdata == "exit":
							try:
								gravity.disable()
							except:
								pass
							break
					if None in gravity.gravity:
						pass
					else:
						payload_hash = hashlib.md5(str(gravity.gravity).encode('utf-8')).hexdigest()
						if (previous_payload_hash is not None):
							if (previous_payload_hash == payload_hash):
								pass
							else:
								previous_payload_hash = payload_hash
								payload = "(x, y, z): " + str(gravity.gravity)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
								time.sleep(0.1)
						else:
							payload = "(x, y, z): " + str(gravity.gravity)
							terminal.insert_text(payload + "\n")
							if (self._data_object.get("protocol") != "terminal"):
								try:
									terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
								except Exception as _exp:
									terminal.insert_text("Exception: " + str(_exp) + "\n")
									return
			#Gyroscope
			elif self._data_object.get("sensor") == "Gyroscope":
				try:
					gyroscope.enable()
				except Exception as _exp:
					terminal.insert_text("Exception: " + str(_exp) + "\n")
					return
				previous_payload_hash = None	
				while True:
					if _data_queue.empty() is False:
						qdata = _data_queue.get()
						if qdata == "exit":
							try:
								gyroscope.disable()
							except:
								pass
							break
					if None in gyroscope.rotation:
						pass
					else:
						payload_hash = hashlib.md5(str(gyroscope.rotation).encode('utf-8')).hexdigest()
						if (previous_payload_hash is not None):
							if (previous_payload_hash == payload_hash):
								pass
							else:
								previous_payload_hash = payload_hash
								payload = "(x, y, z): " + str(gyroscope.rotation)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
								time.sleep(0.1)
						else:
								payload = "(x, y, z): " + str(gyroscope.rotation)
								terminal.insert_text(payload + "\n")
								if (self._data_object.get("protocol") != "terminal"):
									try:
										terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
									except Exception as _exp:
										terminal.insert_text("Exception: " + str(_exp) + "\n")
										return
			else:
				pass
		else:
			while True:
				if _data_queue.empty() is False:
					qdata = _data_queue.get()
					if qdata == "exit":
						break
				payload = "time: " + str(time.strftime("%c", time.gmtime()))
				terminal.insert_text(payload + "\n")
				if (self._data_object.get("protocol") != "terminal"):
					try:
						terminal.insert_text("xmit status: " + self.xmit_payload(payload) + "\n")
					except Exception as _exp:
						terminal.insert_text("Exception: " + str(_exp) + "\n")
						return
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
