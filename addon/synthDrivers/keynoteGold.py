from ctypes import *
import queueHandler
import os
import speech
import synthDriverHandler
import threading
import windowUtils
import wx
from speech import commands
from synthDriverHandler import synthDoneSpeaking, synthIndexReached
# dll path
dllPath = os.path.join(os.path.dirname(__file__), "lib/bst.dll")
# IS_STILL_TALKING message, needed by keynote gold
IS_STILL_TALKING = 957
class CustomWindow(windowUtils.CustomWindow):
	@classmethod
	def _get_className(cls):
		return("KeynoteGoldHWND")
	def __init__(self, dll, handle, *args, **kwargs):
		super(CustomWindow, self).__init__(*args, **kwargs)
		self.dll = dll
		self.dllHandle = handle
	def windowProc(self, window, message, wParam, lParam):
		if message == IS_STILL_TALKING:

			self.dll.bstRelBuf(self.dllHandle)
class SynthDriver(synthDriverHandler.SynthDriver):
	name = "keynoteGold"
	description = "Keynote Gold"
	supportedNotifications = {synthDoneSpeaking, synthIndexReached}
	dll = None
	handle = c_int(0)
	window = None
	@classmethod
	def check(cls):
		return(True)
	def __init__(self, *args, **kwargs):
		super(SynthDriver, self).__init__(*args, **kwargs)
		self.dll = CDLL(dllPath)
		self.dll.bstCreate(byref(self.handle))
		self.window = CustomWindow(self.dll, self.handle, windowName = "KeynoteGoldHWND")
	def terminate(self):
		
		while True:
			try:
				self.dll.bstShutup(self.handle)
				self.dll.bstClose(self.handle)
				self.dll.bstDestroy()
				break
			except:
				pass
		self.window.destroy()
	def _get_supportedSettings(self):
		return([])
	def speak(self, speechSequence, *args, **kwargs):
		speechString = ""
		for i in speechSequence:
			if isinstance(i, str):
				speechString += i
		speechString += "\0"
		threading.Thread(target = self._speak, daemon = True, args = [speechString]).start()
		#self._speak(speechString)
		
	def _speak(self, text):
		while self.dll.TtsWav(self.handle, self.window.handle, text.encode()):
			pass
		queueHandler.queueFunction(queueHandler.eventQueue, synthDoneSpeaking.notify)
		queueHandler.queueFunction(queueHandler.eventQueue, synthIndexReached.notify)
	supportedNotifications = [synthIndexReached, synthDoneSpeaking]
	supportedCommands = {
		commands.IndexCommand
	}
	def _get_language(self):
		return("en")
	def cancel(self):
		self.dll.bstShutup(self.handle)

