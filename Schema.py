from abc import abstractmethod,ABCMeta
from gi.repository import GObject
from WorldState import WorldState
import PSchema
from Action import Action
from Observation import Observation
from TargetAction import TargetAction

class Schema(GObject.Object):
	#__metaclass__ = ABCMeta

	def __init__(self, mem):
		self.preconditions = WorldState()
		self.postconditions =  WorldState()
		self.activations = 0
		self.action = Action()
		self.id  = None
		self.associated_observations = WorldState()
		self.generalised = False
		self.successes = 0
		self.mem = mem

	def add_precondition(self, precondition):
		self.preconditions.add_observation(precondition)

	def add_postcondition(self, postcondition):
		self.postconditions.add_observation(postcondition)

	def add_associated_observation(self, o):
		self.associated_observations.add_observation(o)

	def execute(self):
		if (self.action != None):
			self.action.execute(); self.activations +=1; print "ID: %i ,Activations: %f"%(self.id, self.activations)
		else:
			self.activations +=1
			return 2

	def is_post_pre(self):
		return self.precondition.equal(self.postcondition)


	def equals(self, so2):
		if (self.generalised):
			self.set_vars_from_state(so2.preconditions)
		return self.preconditions.equals(so2.preconditions) and ( (self.action == None and so2.action == None) or (self.action != None and so2.action != None and self.action.equals(so2.action)) ) and self.postconditions.equals(so2.postconditions)

	def satisfies(self, pre2, a2, post2):
		if (self.generalised):
			self.set_vars_from_state(post2)
		return self.preconditions.satisfies(pre2) and (a2 == None or (self.action != None and self.action.equals(a2))) and self.postconditions.satisfies(post2)


	def update(self, ws):
		found_all = True
		for o in self.postconditions.state:
			found = False
			for o2 in ws.state:
				if (o.equals(o2)):
					o.occurred(True)
					found = True
			if (not found):
				o.occurred(False)
				found_all = False
		if(len(self.postconditions.state) == 0):
			for o in ws.state:
				found = False
				for o2 in self.postconditions.state:
					if (o.equals(o2)):
						found = True
				if (not found):
					o.activations =  self.activations
					o.occurred(True)
					self.postconditions.add_observation(o)
					schema_changed = True
		if (len(self.postconditions.state) != len(ws.state)):
			found_all = False
		return found_all

	def copy(self):
		new = Schema(self.mem)
		new.preconditions= self.preconditions.copy()
		new.postconditions = self.postconditions.copy()
		new.action = self.action.copy()
		new.associated_observations = self.associated_observations.copy()
		new.id = int(self.id)
		new.generalised = self.generalised
		new.activations = int(self.activations)
		return new


	def is_synthetic(self):
		for o in self.preconditions.state:
			if (type(o).__name___ == "SyntheticObservation"):
				return True
		return False

	def get_probability(self):
		total = 0; num = 0
		predictions = self.get_predictions()
		for o in predictions.state:
			total += o.get_probability()
			num +=1
		if (num == 0):
			return 1.0
		return total/num

	def to_string(self):
		builder =""
		builder += "\nSchema %d:\n"%int(self.id)
		builder =="=======\n"

		builder +="Activated: %f times,\n"%float(self.activations)

		builder +="\nPre-Conditions:\n"

		builder += self.preconditions.to_string()

		builder += "\nAction:\n"
		if (self.action != None):
			builder +=self.action.to_string()
		else:
			builder += "No action assigned.\n"

		builder +="\nPost-Conditions:\n"
		builder +=self.postconditions.to_string()

		builder +="\nAssociated Observations:\n"
		builder += self.associated_observations.to_string()

		builder += "\n"
		return builder

	def to_xml(self):
		builder = ""
		builder += "<schema id='%d' activations='%f'>\n"%(self.id, self.activations)
		builder += "<preconditions>\n"
		builder += self.preconditions.to_xml()
		builder += "</preconditions>\n"
		if(self.action != None):
			builder += self.action.to_xml()
		builder += "<postconditions>\n"
		builder += self.postconditions.to_xml()
		builder += "</postconditions>\n"
		builder += "<associated_observations>\n"
		builder += self.associated_observations.to_xml()
		builder += "</associated_observations>\n"
		builder += "</schema>\n"
		return builder

	def get_predictions(self):
		return self.postconditions.get_predictions()


	def equals(self, s2):
		return ((self.precondition.equals(s2.precondition)) and self.postcondition.equals(s2.postcondition))

	def set_vars_from_state(self, concrete):
		self.mem.remove_ignored_preconditions(concrete)
		redundant = WorldState(); variables = {}
		if (not self.generalised):
			return redundant
		for o in concrete.state:
			properties = o.get_concrete_properties()
			used = False
			for o2 in self.preconditions.state:
				if (type(o) != type(o2)):
					continue
				properties2 = o2.get_properties()
				for property in properties.keys():
					if (properties2[property] != None):
						v1 = properties[property]
						v2 = properties2[property]
						if("$" in v2 and len(v2) ==2):
							if(not variables.has_key(v2)):
								variables[v2] = v1
								used = True
			if(not used and not o.transitory):
				redundant.add_observation(o)

		for variable in variables.keys():
			value = variables[variable]
			for o in self.preconditions.state:
				o.instantiate_var(variable, value)

			for o in self.postconditions.state:
				o.instantiate_var(variable, value)

			if type(self.action) == type(TargetAction(self)):
				ta = self.action
				for o in ta.target.state:
					o.instantiate_var(variable, value)
		return redundant

GObject.type_register(Schema)