#!/usr/bin/python

# Andrew Koenig, KE5GDB, 12/2016

# This script monitors a 1-wire (DS18B20) temp sensor and
# performs a rolling minimum over n samples. The script will
# then write a macro for an SCom 7330 and write the macro
# to the repeater controller at a given interval.

# Define number of samples to use for rolling minimum. Assume 2 seconds per sample.
samples = 300 # ~10 minutes

# Message update interval (in seconds)
interval = 300

# Moxa IP & Port
ip = "192.168.XX.YY"
port = 1234

# SCom write delay (in seconds)
delay = .01

# SCom master password
password = "MPW"

# User message number
message_number = "0015"

# Imports!
from w1thermsensor import W1ThermSensor
import threading
import logging
import time
import socket

# Define the temp sensor
w1ext = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, "000008a706d6")

ext_temp = 0
ext_temps = []
ext_temp_min = 50

def temp_loop_ext():
	global ext_temp
	global samples
	global ext_temps
	global ext_temp_min
	
	i = 0
	while True:
		# Read the temp sensor
		try:
			ext_temp = w1ext.get_temperature()
			ext_temp = (ext_temp * 9.0 / 5) + 32
		except:
			pass

		# Create a list, and when it is fully populated, perform a rolling update
		if len(ext_temps) < samples:
			ext_temps.append(ext_temp)
			#print "appended!"
		else:
			ext_temps[i] = ext_temp
			#print "replaced " + str(i)
			i = (i + 1) % samples
		
		# Determine the sample period minimum
		ext_temp_min = int(min(ext_temps))
		#print "ext temp:"
		#print str(ext_temp) + " / " + str(int(ext_temp)) + " / " + str(i)
		#print ext_temps
		#print min(ext_temps)
		#print
		
		time.sleep(1)

def macro_loop():
	# Wait for the first temp sample
	time.sleep(5)
	
	global ext_temp_min
	global ip
	global port
	global delay
	
	while True:
		temp = ext_temp_min
		#print temp
		# Detect 1-wire error, abort!
		if temp > 150:
			temp = -1
		if temp < 0:
			temp = -1

		# Start the user message
		macro = password + " 31 " + message_number + " 9710 9961 7020 "
		
		# "One hundred and "
		if temp > 100:
			macro = macro + "0001 0042 0212 "
			temp = temp % 100
		
		# "One Hundred"
		if temp == 100:
			macro = macro + "0001 0042 "
			temp = temp % 100
				
		if temp >= 90:
			macro = macro + "0041 "
			temp = temp % 90
			
		if temp >= 80:
			macro = macro + "0040 "
			temp = temp % 80
			
		if temp >= 70:
			macro = macro + "0039 "
			temp = temp % 70
		
		if temp >= 60:
			macro = macro + "0038 "
			temp = temp % 60
			
		if temp >= 50:
			macro = macro + "0037 "
			temp = temp % 50
			
		if temp >= 40:
			macro = macro + "0036 "
			temp = temp % 40
			
		if temp >= 30:
			macro = macro + "0035 "
			temp = temp % 30
			
		if temp >= 20:
			macro = macro + "0033 "
			temp = temp % 20
			
		if 17 <= temp <= 20:
			macro = macro + "00" + str(temp + 13).rjust(2, '0') + " "	
		
		if 13 <= temp <= 16:
			macro = macro + "00" + str(temp + 12).rjust(2, '0') + " "			

		if 11 <= temp <= 12:
			macro = macro + "00" + str(temp + 11).rjust(2, '0') + " "
			
		if temp == 10:
			macro = macro + "0020 "
		
		if 1 <= temp <= 9:
			macro = macro + "00" + str(temp*2 - 1).rjust(2, '0') + " "

		# "Degrees"  (if temp is OK)
		if temp >= 0:
			macro = macro + "0143 \n\r"
		
		print macro
		#print temp
		# Write macro to SCom. Try/catch in case another client is connected. 
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((ip, port))
			# Poor man's character delay
			for char in macro:
				s.send(char)
				#print char
				time.sleep(delay)
			s.send('\n\r')
			s.close()
		except:
			pass
			

		time.sleep(interval)
		
class MasterThread:
	def __init__(self):
		self.logger=logging.getLogger("MasterThread")
		self.logger.debug("Adding Threads")
		
		self.threads=[]
		self.threads.append(threading.Thread(target=temp_loop_ext))
		self.threads.append(threading.Thread(target=macro_loop))
	def run(self):
		self.logger.info("Enabling all threads")
		self.logger.info("Going Polythreaded")
		for thread in self.threads:
			thread.daemon = True
			thread.start()
	        #we need this thread to keep ticking
		try:
			while(True):
				if not any([thread.isAlive() for thread in self.threads]):
					print "Thread dead!"
					break
				else:
					time.sleep(1)
		except (KeyboardInterrupt, SystemExit):
			print "Exiting!"
		self.logger.info("All threads have terminated, exiting main thread...")
if __name__=="__main__":
	logging.basicConfig(level=logging.WARNING)
	threadCore = MasterThread()
	threadCore.run()
