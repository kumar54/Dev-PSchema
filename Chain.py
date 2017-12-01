from gi.repository import GObject

class Chain(GObject.Object):


	def __init__(self):
		self.sequence = []
		self.activations = 0.0
		self.successes = 0.0
		self.excitation = 0.0
		self.execution_ID = []
		#print "Pair type:", type(self)


	def equals(self, chain2):
		return self.sequence == chain2.sequence

	

	def to_xml(self):
		"""Return Chains in XML format"""
		builder = ""; c = " "
		for a in self.sequence:
			c +="%s "%str(a)
		builder += "<Chain  activations='%f' successes = '%f' sequence = '%s'  />\n"%(self.activations, self.successes, c)
		return builder


	def parse_node(self, node):
		for k1 in node.attrib.keys():
			value = node.attrib[k1]
			#print "\n",node.tag, node.tag, k1,"*",value,"*"
			if k1 =="sequence":
				d = []; z = ""; no = False
				for a1 in value:
					#print "Sub value is :", a1
					if a1 != ' ':
						z +=a1; no = True
					else:
						if no:
							#print "No is:", z
							no = int(z); z = ""
							d += [no]; no = False
				self.sequence = d
			if k1 =="activations":
				self.activations = float(value)
			if k1 == "successes":
				self.successes = float(value)
			if k1 == "excitation":
				self.excitation = float(value)
		#print "Sequence in chain is: ", self.sequence

	def copy(self):
		c2 = Chain()
		c2.sequence = list(self.sequence)
		c2.activations = self.activations
		c2.successes = self.successes
		c2.excitation = self.excitation
		c2.execution_ID = list(self.execution_ID)
		return c2

GObject.type_register(Chain)