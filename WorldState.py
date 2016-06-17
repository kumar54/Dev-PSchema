from gi.repository import GObject


class WorldState(GObject.Object):

	def __init__(self):
		self.state = []


	def add_observation(self, o):
		found = False; condition = False
		for o2 in self.state:
			if (o.equals(o2)):
				o2.activations +=1; found = True
				condition = ( o2.is_generalised() and (type(o2) == type(o)) )
				break
		if (not found or condition):
			self.state.append(o)

	def remove_observation(self, o):
		self.state.remove(o)

	def remove_observation_with_id(self, id):
		for o in self.state:
			if (o.sensor_id == id):
				self.state.remove(o)

	def equals(self, ws2):
		return self.satisfies(ws2) and len(ws2.state) == len(self.state)


	def satisfies(self, ws2= None):
		#print self.to_string(),"Satisfies",ws2.to_string()
		if (ws2 == None):
			return True
		for o in ws2.state:
			found = False
			for o2 in self.state:
				if (o.equals(o2)):
					found = True
					break
			if (not found):
				return False
		return True


	def type_subset(self, ws2):
		found = True
		for o in ws2.state:
			found = False;
			for o2 in self.state:
				if (type(o) == type(o2)):
					found = True
					break
			if (not found):
				return False;
		return found


	def equivalents(self, ws2= None):
		#print "\nSelf:",self.to_string(),"--------------\n", ws2.to_string()
		if len(self.state) != len(ws2.state):
			return False
		for o in ws2.state:
			found = False; same = 0
			for o2 in self.state:
				if (type(o) == type(o2) and not found):
					found = True
				else:
					continue
			if (not found):
				return False
		return True

	def print_to(self):
		message = "\n"
		for o in self.state:
			message += str(o.to_string())
		print message


	def copy(self):
		ws = WorldState()
		for o in self.state:
			ws.add_observation(o.copy())
		return ws


	def get_predictions(self):
		predictions = {}
		for o in self.state:
			if ( predictions.has_key(o.sensor_id)):
				if (predictions[o.sensor_id].get_probability() < o.get_probability()):
					predictions[o.sensor_id] =  o
			else:
				predictions[o.sensor_id] = o
		ws = WorldState()
		for sensor_id in predictions.keys():
			ws.add_observation(predictions[sensor_id])
		return ws

	def to_string(self):
		builder = ""
		for o in self.state:
			builder +=o.to_string()
		return builder

	def to_xml(self):
		builder = ""
		builder += "<worldstate>\n"
		for o in self.state:
			builder += o.to_xml()
		builder += "</worldstate>\n"
		return builder

	def get_probability(self):
		probability = 1
		predictions = self.get_predictions()
		for o in predictions.state:
			probability *= o.get_probability()
		return probability

	def complement(self, ws2, sensor_complement):
		complement_state = WorldState()
		ws2_predictions = ws2.get_predictions()
		for o in ws2_predictions.state:
			matched = False;
			predictions = self.get_predictions()
			for o2 in predictions.state:
				if(sensor_complement):
					if (o.sensor_id == o2.sensor_id and type(o) == type(o2)):
						matched = True
				else:
					if (o.equals(o2)):
						matched = True
			if (not matched):
				complement_state.add_observation(o.copy())
		return complement_state


	def union(self, ws2):
		comp = complement(ws2, False)
		u = self.copy()
		for o in comp.state:
			u.add_observation(o.copy())
		return u

	def intersection(self, ws2):
		n =  WorldState()
		for o in self.state:
			matched = False;
			for o2 in ws2.state:
				if (o2.equals(o)):
					matched = True
			if (matched):
				n.add_observation(o)
		return n


	def inst_vars(self, concrete_states):
		variables = {}
		for o in concrete_states.state:
			properties = o.get_properties()
			for p in properties.keys():
				if (not variables.has_key(p)):
					variables[p] = properties[p]
		for variable in variables.keys():
			v = variables[variable]
			for o in self.state:
				props = o.get_properties()
				for p in props.keys():
					p_val = props[p]; reply = None
					if(p == variable and len(p_val) < 3):
						o.set_property_var(p, v)
					elif (p == variable and len(p_val) > 2 and len(p) < 3):
						sym = p_val[2]; q = int(v)
						s = "0%c"%p_val[3]; w = int(s)
						if (sym =='-'):
							reply = q-w
						else:
							reply = q+w
					ss = str(abs(reply))
					o.set_property_var(p, ss)
		return variables

GObject.type_register(WorldState)