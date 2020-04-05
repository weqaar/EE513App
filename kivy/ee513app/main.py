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
from plyer import vibrator
from plyer import accelerometer
import threading
import time
import queue


class MainScreen(GridLayout):

	#global _data_object  
	#global global_terminal
	#global _data_queue

	_data_object = { "server": None,
					"port": None,
					"protocol": None,
					"platform": str(platform)
			   }
		
	def __init__(self, **kwargs):
		super(MainScreen, self).__init__(**kwargs)
	
		self.cols = 1
		self.rows = 1

		self._data_queue = queue.Queue()

		#Layouts
		self._main_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 1))
		_terminal_layout = BoxLayout(orientation='vertical', padding=0, size_hint=(1, 0.2))
		_partition_layout = GridLayout(cols=2, rows=4, padding=0, size_hint=(1, 1), row_force_default=True, \
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

	def publish_terminal(self, terminal, _data_queue):
		while True:
			if _data_queue.empty() is False:
				qdata = _data_queue.get()
				if qdata == "exit":
					break
			if (platform == 'android') or (platform == 'ios'):
				vibrator.vibrate(2)
				accelerometer.enable()
				terminal.insert_text("sensor: " + str(accelerometer.acceleration) + "\n")
				time.sleep(0.5)
			else:
				terminal.insert_text("time: " + str(time.strftime("%c", time.gmtime())) + "\n")
				time.sleep(2)
  
class AXLApp(App):

	def build(self):
		return MainScreen()
		
		
if __name__ == "__main__":
	AXLApp().run()
