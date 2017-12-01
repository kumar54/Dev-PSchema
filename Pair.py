from gi.repository import GObject

class Pair(GObject.Object):

	def __init__(self, T1, T2):
		self.first = T1
		self.second = T2
		#print "Pair type:",type(self)

	def __iter__(self):
		yield self.first
		yield self.second

	def equals(self, p2):
		return self.first == p2.first and self.second == p2.second

	def __str__(self):
		return "%s, %s"%(str(self.first),str(self.second))
