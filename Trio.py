from gi.repository import GObject

class Trio(GObject.Object):

	def __init__(self, T1, T2, T3):
		self.first = T1
		self.second = T2
		self.third = T3
		#print "Pair type:",type(self)
		self.i = 0

	def __iter__(self):
		yield self.first
		yield self.second
		yield self.third

	def equals(self, p2):
		return self.first == p2.first and self.second == p2.second and self.third == p2.third

	def to_string(self):
		return self.first, self.second, self.third

	def next(self):
        	if self.i ==0:
			self.i +=1
			return self.first
		elif self.i == 1:
			self.i +=1
			return self.second
		elif self.i == 2:
			self.i +=1
			return self.third
        	else:
			self.i = 0
            		raise StopIteration()

	def __eq__(self, other):
        	return self.equals(other)
