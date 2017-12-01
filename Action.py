from gi.repository import GObject
import xml
from Coordinates import Coordinates

class Action(GObject.Object):
	#__metaclass__ = abc.ABCMeta
	__gsignals__ = {
			"abstract_signal" : (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ( GObject.TYPE_OBJECT,))
	}

	def __init__(self):
		GObject.Object.__init__(self)
		self.props = {}
		self.props_var = {}
		self.name = None
		self.coords = Coordinates()


	def get_properties(self):
		"""Get Dictionary containing propserties
		Variable value is returned if exists else concrete is returned"""
		props = {}
		for p in self.props.keys():
			if self.props_var.has_key(p) and self.props_var[p] != None:
				props[p] = self.props_var[p]
			else:
				props[p] = self.props[p]
		return props


	def get_var_properties(self):
		"""Returns variable properties of the observation"""
		props = {}
		for p in self.props_var.keys():
			if self.props_var[p] != None:
				props[p] = self.props_var[p]
			else:
				props[p] = self.props[p]
		return props

	def get_concrete_properties(self):
		"""Returns concrete properties, having concrete value not generalised"""
		props = {}
		for p in self.props.keys():
			if self.props[p] != None:
				props[p] = self.props[p]
			else:
				props[p] = self.props_var[p]
		return props

	def equals(self, a2,ignore = False):
		"""Returns True if two actions are equal"""
		if self.name != a2.name:
			return False
		props = self.get_concrete_properties(); props2 = a2.get_concrete_properties()
		for p2 in props2.keys():
			if not(props.has_key(p2)):
				return False
			if (type(props[p2]) == type(props2[p2]) == type(float())):
				if abs(abs(props[p2]) - abs(props2[p2])) > 0:
					return False
			elif (props[p2] != props2[p2]):
				return False
		if ignore:
			return True
		if not self.coords.equals(a2.coords):
			return False
		return True


	def similar(self, a2):
		"""Returns True if two actions have same name"""
		if a2.name != self.name:
			return False
		props = self.get_concrete_properties(); props2 = a2.get_concrete_properties()
		for p2 in props2.keys():
			if not(props.has_key(p2)):
				return False
			if props[p2] != props2[p2]:
				return  False
		#print "Observation equals: ", props, props2
		return True


	def execute(self):
		"""Execute action with abstract signal"""
		#print "Emitting action signal:", self.name, self.props,self.coords.concrete_coords
		self.emit("abstract_signal", self)


	def repeat(self):
		"""Emit abstract signal"""
		self.emit("abstract_signal", self)
		print "Repeating abstract signal with parameters: ", self.props, self.coords.concrete_coords


	def set_concrete_prop(self, name, val):
		"""Set value for the concrete property"""
		try:
			value = float(val)
		except:
			try:
				value = int(val)
			except:
				value = str(val)
		if name == "x" or name == "y":
			self.coords.set_concrete_coords(name, value)
			return
		self.props[name] = value
		#print "Setting in action: ", name, self.props[name], self.props_var[name]

	def set_property_var(self, name, val):
		"""Set value for the variable properties"""
		try:
			value = float(val)
		except:
			try:
				value = int(val)
			except:
				value = str(val)
		#print "@set_priop_val:", name, value
		if name == "x" or name == "y":
			self.coords.set_variable_coords(name, value)
			return
		self.props_var[name] = value
		self.props[name] = None


	def copy(self):
		"""Create copy of the action"""
		a2 = Action()
		a2.name = str(self.name)
		a2.props = self.props.copy()
		a2.props_var = self.props_var.copy()
		a2.coords = self.coords.copy()
		#a2.connect("abstract_signal")
		return a2

	def to_string(self):
		"""Returns action as string to print"""
		act = "<action type='%s' name='%s' "%(str(type(self).__name__), self.name)
		prop = self.get_properties()
		for p in prop.keys():
			act += " %s= '%s' "%(p, prop[p])
		coords = self.coords.get_coords()
		for prop in coords.keys():
			act += "%s= '%s' "%(prop, coords[prop])
		act += " /> \n"
		return act


	def to_concrete_string(self):
		"""Returns action as string to print"""
		act = "<action type='%s' name='%s' "%(str(type(self).__name__), self.name)
		prop = self.get_concrete_properties()
		for p in prop.keys():
			act += " %s= '%s' "%(p, prop[p])
		coords = self.coords.get_concrete_coords()
		#print "Concrete Action:", self.get_concrete_properties(), self.coords.get_concrete_coords()
		for prop in coords.keys():
			act += "%s= '%s' "%(prop, coords[prop])
		act += " /> \n"
		return act

	def to_xml(self):
		"""Returns action in XML format"""
		builder = ""
		builder += "<action name='%s' "%(self.name) #str(type(self).__name__),
		properties = self.get_properties()
		for prop in properties.keys():
			builder += "%s='%s' "%(prop, properties[prop])
		coords = self.coords.get_coords()
		for prop in coords.keys():
			builder += "%s= '%s' "%(prop, coords[prop])
		builder += " />\n"
		return builder


	def parse_node(self, node):
		"""Create elememts of the action from XML format"""
		for k in node.attrib.keys():
			value = node.attrib[k]
			if  k == "type":
				continue
			if k == "name":
				self.name = str(value)
			elif k !="type":
				if type(value) == type(str()):
					if value[0] == '$':
						self.set_property_var(k, value); continue
					else:
						self.set_concrete_prop(k, value); continue
				else:
					self.set_concrete_prop(k, value); continue



	def instantiate_var(self, variable, value):
		"""Instantiates the property (variable) with given value """
		#print "@intantiate_var Instantiating: ",self.sensor_id, variable, value
		props = self.get_properties()
		coords = self.coords.get_coords()
		props.update(coords)
		#print "@intantiate_var Instantiating: ",props, self.coords.get_coords(), variable, value
		for p in props.keys():
			if p != variable:
				continue
			try:
				p_val = float(props[p])
			except:
				try:
					p_val = int(props[p])
				except:
					p_val = str(props[p])
			#print "Values to be instantiated:", p, props[p], p_val, type(p_val) #!= type(str()) and "$" in p_val, (p_val == variable and len(p_val)<3)  (len(p_val)>2 and p == variable)
			if type(p_val) != type(str()) or not("$" in p_val):
				continue
			#print "$ sign found:", "$" in p_val, p_val
			#if not("$" in p_val):
			#	continue
			if (not "-" in p_val) and (not "+" in p_val):
				#print "Setting concrete_values: ", p, value
				self.set_concrete_prop(p, value)
			else:#elif(str(p_val) != str(variable) and len(p_val)>2):
				#print "Property with function to be changed:", p, p_val, value
				if type(value) != type(float()):
					return
				try:
					sym = p_val[p_val.index("-")]
				except:
					sym = p_val[p_val.index("+")]
				#sym = p_val[2]
				q = float(value); reply = None
				# s = "0%c"%p_val[3]; w = float(s)
				w = float(p_val[p_val.index(sym)+1:])
				if (sym =='-'):
					reply = q-w
				else:
					reply = q+w
				ss = abs(reply)
				#print "setting concrete Value with function created: ",p, ss
				self.set_concrete_prop(p, ss)


GObject.type_register(Action)