from gi.repository import GObject

class Pair(GObject.Object):

	def __init__(self, T1, T2):
		self.first = T1
		self.second = T2
		#print "Pair type:",type(self)

	def equals(self, p2):
		return self.first == p2.first and self.second == p2.second
