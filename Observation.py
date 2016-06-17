import xml
from abc import abstractmethod,ABCMeta
from gi.repository import GObject
class Observation(GObject.Object):

	def __init__(self):
		GObject.Object.__init__(self)
		self.observations = []
		self.activations = 0
		self.successes = 0
		self.sensor_id = None
		self.transitory = False
		self.memory_limit = 100
		self.generalised = False



	def get_all_obs(self):
		for o in self.observations:
			print o

	def to_string(self):
		builder = ""
		builder += "%s, "%type(self).__name__
		prop = self.get_properties()
		for p in prop.keys():
			builder += "%s: %s, "%(p,prop[p])
		builder += "\n"
		return builder

	def to_xml(self):
		builder = ""
		builder += "<observation type='%s' "%type(self).__name__
		properties = self.get_properties()
		for prop in properties.keys():
			builder += "%s='%s' "%(prop, properties[prop])
		builder += "successes='%f' activations='%f' sensor_id='%d' />\n"%(self.successes, self.activations, self.sensor_id)
		return builder


	def get_probability(self):
		if (self.activations == 0):
			return 1
		return self.successes/self.activations

	def parse_node(self, node):
		for child in node.iter():
			for grand in child.attrib.keys():
				value = child.attrib[grand]
				if (grand == "activations"):
					self.activations = float(value)
				elif (grand == "successes"):
					self.successes = float(value)
				elif (grand == "sensor_id"):
					self.sensor_id = int(value)
				elif (grand == "parent"):
					self.parentId = int(value)
				elif (grand != "type"):
					if(value[0] == '$'):
						self.set_property_var(grand, value)
					else:
						self.set_concrete_var(grand, value)

	def occurred(self, success):
		if(self.activations >= self.memory_limit):
			if(success):
				if (self.successes < self.memory_limit):
					self.successes +=1
			elif (self.successes > 0):
				self.successes -=1
		else:
			if(success):
				self.successes += 1
			self.activations +=1


	def instantiate_var(self, variable, value):
		if(not ("$" in variable)):
			return
		props = self.get_properties()
		for p in props.keys():
			p_val = props[p]
			if(p_val == variable):
				self.set_concrete_var(p, value)
			elif (len(p_val)>2 and p_val[0:2] == variable):
				sym = p_val[2]; q = int(value); reply = None
				s = "0%c"%p_val[3]; w = int(s)
				if (sym =='-'):
					reply = q-w
				else:
					reply = q+w
				ss = abs(reply)
				self.set_concrete_var(p, ss);

	def hash(self):
		builder = ""
		builder +="%s"%str(type(self))
		properties = self.get_properties()
		for prop in properties.keys():
			builder += "%s%s, "%(prop, properties[prop])
		return builder

	def is_generalised(self):
		props = self.get_properties()
		for p in props.keys():
			if("$" in props[p][0]):
				return True
		return False