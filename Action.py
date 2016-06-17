from gi.repository import GObject
import xml
class Action(GObject.Object):
	#__metaclass__ = abc.ABCMeta

	#def __init__(self):
	#	GObject.Object.__init__(self)

	def to_string(self):
		act = "<action type='%s' "%str(type(self).__name__)
		prop = self.get_properties()
		for p in prop.keys():
			act += " %s= '%s'"%(p, prop[p])
		act += " /> \n"
		return act

	def to_xml(self):
		builder = ""
		builder += "<action type='%s' "%type(self).__name__
		properties = self.get_properties()
		for prop in properties.keys():
			builder += "%s='%s' "%(prop, properties[prop])
		builder += " />\n"
		return builder


	def parse_node(self, node):
		for k in node.attrib.keys():
			self.set_concrete_var(k, node.attrib[k])

	def similar(self, act2):
		if type(self) == type(act2):
			return True