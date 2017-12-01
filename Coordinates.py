from gi.repository import GObject

class Coordinates(GObject.Object):


	def __init__(self):
		self.concrete_coords = {}
		self.variable_coords = {}



	def get_coords(self):
		ps = {}
		for p in self.concrete_coords.keys():
			if self.variable_coords.has_key(p) and self.variable_coords[p] != None:
				ps[p] = self.variable_coords[p]
			else:
				ps[p] = self.concrete_coords[p]
		return ps

	def get_concrete_coords(self):
		coords = {}
		for k in self.concrete_coords.keys():
			#print "Concrete coords:", k, self.concrete_coords[k]
			if self.concrete_coords[k] != None:
				coords[k] = self.concrete_coords[k]
			else:
				coords[k] = self.variable_coords[k]
		return  coords


	def get_variable_coords(self):
		coords = {}
		for k in self.concrete_coords.keys():
			if self.variable_coords[k] != None:
				coords[k] = self.variable_coords[k]
			else:
				coords[k] = self.concrete_coords[k]
		return  coords

	def set_concrete_coords(self, p, value):
		self.concrete_coords[p] = value


	def set_variable_coords(self, p, value):
		self.variable_coords[p] = value
		if not self.concrete_coords.has_key(p):
			self.concrete_coords[p] = None


	def equals(self, coords2):
		for p in coords2.concrete_coords.keys():
			#print "Coords match:",self.concrete_coords[p], coords2.concrete_coords[p], self.concrete_coords.has_key(p), self.concrete_coords[p] == coords2.concrete_coords[p]
			if not(self.concrete_coords.has_key(p) and self.concrete_coords[p] == coords2.concrete_coords[p]):
				return False
		return True


	def similar(self, coords2):
		for p in coords2.concrete_coords.keys():
			if not(self.concrete_coords.has_key(p)):
				return False
		return True


	def copy(self):
		c2 = Coordinates()
		c2.concrete_coords = dict(self.concrete_coords)
		c2.variable_coords = dict(self.variable_coords)
		return c2


	def get_similarity(self, coords2):
		sim = 1.0; m = 0.0; len_coords = len(coords2.concrete_coords.keys())
		if len_coords > 0:
			m = 1.0/len_coords
		elif len(self.concrete_coords.keys()) == 0:
			return 1.0

		for p in coords2.concrete_coords.keys():
			diff = 0.0
			if self.concrete_coords.has_key(p) and coords2.concrete_coords.has_key(p) and self.concrete_coords[p] != None and coords2.concrete_coords[p] !=None:
				p1 = coords2.concrete_coords[p]; p2 = self.concrete_coords[p]
				#set = min(p1, p2)/(max(p1, p2)+0.00000001)
				#set = round(set, 2)
				#if 0.8 < set < 1.2:
				#	sim += m
				#print "coordinates similarity:", self.concrete_coords[p], coords2.concrete_coords[p]
				diff = abs(coords2.concrete_coords[p] - self.concrete_coords[p])
				#sim -= m/(2.0+diff)
				if diff:
					sim -= m/2.0
					#sim -= m/(2.0+diff)
				#print "Coords Sim:", p, coords2.concrete_coords[p], self.concrete_coords[p], sim
			else:
				sim -= m
		#print "Coordniates similarity:",self.concrete_coords, coords2.concrete_coords, sim
		return sim

	def to_string(self):
		b = ""
		for p in self.concrete_coords.keys():
			if self.variable_coords.has_key(p) and self.variable_coords[p] != None:
				b += "%s='%s' "%(p, self.variable_coords[p])
			else:
				b += "%s='%f' "%(p, self.concrete_coords[p])
		return b


