from gi.repository import GObject
import PSchema, sys
from WorldState import WorldState
from Action import Action
class TargetAction(Action):

	__gsignals__ = {
			"target_signal" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (WorldState, GObject.TYPE_INT,))
	}

	def __init__(self, mem):
		Action.__init__(self)
		self.target = WorldState()
		self.parentId = None
		self.m = mem


	def to_string(self):
		return "Target action: %s\n"%self.target.to_string()


	def to_xml(self):
		return "<action type='target' parent='%d'>%s</action>\n"%(self.parentId, self.target.to_xml())

	def equals(self, a2):
		if(type(a2) != type(self)):
			return False
		return self.parentId == a2.parentId


	def execute(self):
		excluded = [self.parentId]
		#print self.target.to_string(), self.parentId
		a =  self.target.__gtype__
		#self.emit("target_signal", self.target, excluded)
		self.m.achieve_target(self.target, self.parentId)

	def set_concrete_var(self, name, val):
		if (name == "parent"):
			self.parentId = int(val)

	def copy(self):
		a = TargetAction(self.m)
		a.target = self.target.copy()
		a.parentId = self.parentId
		return a

	def get_properties(self):
		props = {}
		props["parent"] = str(self.parentId)
		return props

#GObject.type_register(TargetAction)