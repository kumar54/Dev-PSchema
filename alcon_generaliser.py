from gi.repository import GObject
from WorldState import WorldState
from TargetAction import TargetAction
from Pair import Pair
import random
class AlConGeneraliser(GObject.Object):

	def __init__(self, memory):
		self.mem = memory


	def assimilate(self, schema, schemas):
		similar = []
		similar.append(schema)
		action = TargetAction(self.mem)
		target_used = True
		min_size = len(schema.preconditions.state)

		if(min_size == 0 or schema.generalised):
			return 1

		similar_action_states = WorldState()
		state_size = 100
		for schema2 in schemas:
			if (schema2.generalised or schema.id == schema2.id):
				continue
			if (self.state_types_match(schema.preconditions, schema2.preconditions) and
				self.state_types_match(schema.postconditions.get_predictions(), schema2.postconditions.get_predictions())):
				similar.append(schema2)
			
			if (schema.action.similar(schema2.action)):
				post_len = len(schema2.postconditions.state)
				if (state_size > post_len):
					similar_action_states = schema2.postconditions
					state_size = len(schema2.postconditions.state)

			if(len(schema.action.get_properties()) == 0):
				action = schema.action.copy();
				self.mem.emit("connect_action", action, type(action).__name__)
				target_used = False
			else:
				if (schema.action.equals(schema2.action)):
					predictions = schema2.get_predictions()
					if len(schema2.preconditions.state) <= min_size and len(predictions.state) > 0 and schema.preconditions.satisfies(schema2.preconditions):
						min_size = len(schema2.preconditions.state)
						action.target = schema2.postconditions.get_predictions().copy();
		total = len(similar)
		if (total < 2):
			return 2;
		same_action_length = len(similar_action_states.state)
		if (same_action_length ==0 or same_action_length >= len(schema.postconditions.state)):
			return 3
		if (target_used and action.target == None):
			return 4
		state_props = {}
		for o in similar_action_states.state:
			props = o.get_properties()
			for prop in props.keys():
				if (not state_props.has_key(prop)):
					state_props[prop] = props[prop]
		variables = {}; pvars = {}
		post_copy = schema.postconditions.copy()
		#for s in similar:
		for o in schema.preconditions.state:
			properties = o.get_properties()
			for property in properties.keys():
				print ""
				f_pvar = False; f_prop = False; f_prop_val = False
				v = properties[property]
				f_pvar_str = None; f_pvar_val = None
				for pvar in variables.keys():
					pair = variables[pvar]
					if (pair.first == property):
						f_prop = True
						if (pair.second == v):
							f_prop_val = True; break
						elif (len(pvar)<3):
							f_pvar_str = pvar
							f_pvar_val = pair.second
				if (f_prop and not f_prop_val):
					func = self.find_relation(v, f_pvar_val, property)
					answer = ""
					if ("-" in func):
						answer = "%s+%c"%(f_pvar_str,func[1])
					else:
						answer = "%s-%s"%(f_pvar_str, func)
					com = Pair(property,v)
					com.first = property; com.second = v; variables[answer] = com
				elif (f_prop and f_prop_val):
					continue
				else:
					diff = self.diff_props_in_similar(property, properties[property], similar, schema.id)
					if state_props.has_key(property) and state_props[property] != None:
						in_basic =  state_props[property]

					if (not diff and not state_props.has_key(property)):
						print "Property disqualified:",property
						continue
					pvar = "$%c"%random.randint(97,122)

					while(pvars.has_key(pvar)):
						pvar = "%c"%random.randint(97,122)
					com = Pair(property,v)
					com.first = property; com.second = v
					variables[pvar] = com; pvars[pvar] = v
		if(len(variables) == 0):
			return 9
		trial_schema = schema.copy()
		trial_schema.action = action.copy()

		trial_schema.generalised = True
		self.generalise_state(trial_schema.postconditions.state, variables)
		if(target_used):
			predictions = trial_schema.action.target.get_predictions()
			self.generalise_state(predictions.state, variables)
		else:
			self.mem.emit("connect_action", trial_schema.action, type(trial_schema.action).__name__)
		self.generalise_state(trial_schema.preconditions.state, variables)
		if(self.generalisation_exists(trial_schema, schemas)):
			print "Generalised schema already exists in another form."
			return 5
		self.mem.add_schema(trial_schema)
		if(target_used):
			trial_schema.action.parentId = trial_schema.id
		return 6



	def assimilate_association(self, latest, associations):
		if (self.mem.is_ignored(latest.first.sensor_id) or self.mem.is_ignored(latest.second.sensor_id)):
			return;
		similar_associations = []
		go = latest.first.copy()
		different_props = []
		l_props = latest.first.get_properties()
		for p in associations.keys():
			if (self.mem.is_ignored(p.first.sensor_id) or self.mem.is_ignored(p.second.sensor_id)):
				continue
			if (type(p.first) == type(latest.first) and p.second.equals(latest.second)):
				props = p.first.get_properties()
				for prop in props.keys():
					if (l_props[prop] != props[prop]):
						if(not prop in different_props):
							different_props.append(prop)
				similar_associations.append(p)
		total = len(similar_associations)
		if (total < 2):
			return
		if (len(different_props) == len(go.get_properties()) or len(different_props) == 0):
			return
		last_var = 96;
		for prop in different_props:
			last_var +=1
			pvar = "$%c"%last_var
			go.set_property_var(prop, pvar)
		gp = Pair(go, latest.second)
		self.mem.add_generalised_associations(gp)


	def generalise_state(self, state, variables):
		for o in state:
			properties = o.get_properties()
			for property in properties.keys():
				v1 = properties[property]
				for pvar in variables.keys():
					pair_v2 = variables[pvar]
					if (pair_v2.first == property):
						if (pair_v2.second == v1):
							o.set_property_var(property, pvar)
						else:
							fx = None; answer = None
							fx = self.find_relation(v1, pair_v2.second, property)
							if (fx != None):
								if ("-" in fx):
									answer = "%s+%c"%(pvar,fx[1])
								else:
									answer = "%s-%s"%(pvar,fx)
							else:
								answer = pvar
							o.set_property_var(property, answer)
		return


	def state_types_match(self, ws, ws2):
		if (len(ws.state) != len(ws2.state)):
			return False
		ws2c = ws2.copy(); wsc = ws.copy()
		for o in wsc.state:
			match1 = False;
			for o2 in ws2c.state:
				if (type(o) == type(o2)):
					match1 = True
			if (not match1):
				return False
		return True


	def generalisation_exists(self, test_schema, schemas):
		exists = False
		for s2 in schemas:
			if(not s2.generalised):
				continue
			if(not self.state_types_match(test_schema.preconditions, s2.preconditions) or not self.state_types_match(test_schema.postconditions.get_predictions(), s2.postconditions.get_predictions())):
				exists = False; continue
			else:
				exists = True
			variable_map = {}
			if(not self.matching_generalised_states(test_schema.preconditions, s2.preconditions, variable_map)):
				exists = False; continue
			if(type(test_schema.action) == type(TargetAction(self.mem)) and type(s2.action) == type(TargetAction(self.mem))):
				target1 = test_schema.action.target.get_predictions()
				target2 = s2.action.target.get_predictions()
				if(not self.matching_generalised_states(target1, target2, variable_map)):
					continue
			else:
				if(not test_schema.action.equals(s2.action)):
					continue
			return True
		return False


	def find_relation(self, p1, p2, prop):
		if (len(prop) < 2 and p2 != None):
			m = int(p2) - int(p1)
			n = str(m)
			return n
		else:
			return None


	def matching_generalised_states(self, ws, ws2, variable_map):
		for o in ws.state:
			props1 = o.get_properties()
			for o2 in ws2.state:
				props2 = o2.get_properties()
				if ((o) == type(o2)):
					for property in props1.keys():
						v1 = props1[property]
						v2 = props2[property]
						if("$" in v1 and "$" in v2):
							if(variable_map.has_key(v1) and variable_map[v1] != None and v2 != variable_map[v1]):
								return False
							variable_map.set(v1, v2)
						elif (v1 != v2):
							return False
		return True


	def diff_props_in_similar(self, property, val, similar, origin_id):
		#print "Property check:", property, val, origin_id
		for s in similar:
			if(s.id == origin_id):
				continue
			for o in s.preconditions.state:
				properties = o.get_properties()
				if (properties.has_key(property) and properties[property] != val):
					return True
		return False
