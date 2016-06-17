from gi.repository import GObject, Gtk
from Schema import Schema
from WorldState import WorldState
from Action import Action
from Observation import Observation
from TargetAction import TargetAction
from alcon_generaliser import AlConGeneraliser
from Pair import Pair
from chains import Chains
from syntheticobservation import SyntheticObservation
#from VisualObservation import VisualObservation
from novelty_calculator import NoveltyCalculator
import xml.etree.ElementTree as ET
import xml, time

class Memory(GObject.Object):
	__gsignals__ = {
				"connect_action" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (Action, str,)),
				"create_action" : (GObject.SIGNAL_RUN_LAST, Action, (str,)),
				"create_observation" : (GObject.SIGNAL_RUN_LAST, Observation, (str,)),
				"update_state" : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ())
	}




	def __init__(self):
		GObject.Object.__init__(self)
		self.schemas = []
		self.ignored_preconditions = []
		self.observations = {}
		self.generalised_associations = {}
		self.chains = []
		self.current_schema = None
		self.current_chain = None
		self.Generaliser = None
		self.ExcitationCalculator = None
		self.ws = None
		self.predicted_world_state = None
		self.associations = {}
		self.total_generalised_schema_executions = 0
		self.successful_generalised_schema_executions = 0
		self.loading_schema = None
		self.loading_state_type = None
		self.next_id = 0
		self.excitation_calculator = NoveltyCalculator(self)
		self.generaliser = AlConGeneraliser(self)


	def add_schema(self, s):
		self.schemas.append(s)
		s.id = self.next_id
		self.next_id +=1

	def add_chain(self, new_chain):
		found = False
		if len(self.chains) > 0 :
			for chainx in self.chains:
				if chainx.chain == new_chain:
					found = True
			if (not found):
				print "Chain not match:",new_chain
				C = Chains(new_chain)
				self.chains.append(C)
				return
		else:
			C = Chains(new_chain)
			self.chains.append(C)
			return


	def get_chain_from_chain(self, chain):
		for C in self.chains:
			if C.chain == chain.chain:
				return C
		print "Chain not found"

	def get_schema_from_action(self, action):
		return self.get_schema(self.ws, action, WorldState())

	def get_schema_from_id(self, id):
		return self.schemas[id]


	def remove_ignored_preconditions(self, pres):
		remove = []
		for o in pres.state:
			for sensor_id in self.ignored_preconditions:
				if(sensor_id == o.sensor_id):
					remove.append(o)
		for o in remove:
			pres.state.remove(o)


	def is_ignored(self, sensor_id):
		try:
			self.ignored_preconditions.index(sensor_id)
		except:
			return False
		return True

	def ignore_precondition(self, sensor_id):
		self.ignored_preconditions.append(sensor_id)



	def remove_transitory_observations(self, ws):
		remove = []
		for o in ws.state:
			if (o.transitory):
				remove.append(o)
		for o in remove:
			ws.state.remove(o)

	def get_schema(self, preconditions, action, postconditions):
		self.remove_ignored_preconditions(preconditions)
		found_schema = None
		for schema in self.schemas:
			if (schema.satisfies(preconditions, action, postconditions)):
				found_schema = schema
				probability = schema.get_probability()
				return found_schema
		return found_schema


	def get_all_schemas(self):
		all_schemas = list(self.schemas)
		return all_schemas


	def get_or_create_schema(self, preconditions, action, postconditions, use_action = True):
		self.remove_ignored_preconditions(preconditions)
		if (use_action):
			found_schema = self.get_schema(preconditions, action, postconditions)
		else:
			found_schema = self.get_schema(preconditions, None, postconditions)
		if (found_schema == None):
			found_schema = Schema(self)
			found_schema.preconditions = preconditions
			if (use_action):
				found_schema.action = action
			found_schema.postconditions = postconditions
			self.add_schema(found_schema)
		return found_schema


	def update_world_state(self, new_state):
		prev_state = WorldState()
		if (self.ws != None):
			prev_state = self.ws
		self.ws = new_state.copy()
		if (self.current_schema == None):
			return 0
		wsc = self.ws.copy()
		if self.current_schema !=None:
			print "Current schemas @ update: ",self.current_schema.id
		if self.current_chain != None:
			print "Current Chain @ update: ", self.current_chain.chain
		else:
			print "No current chain @ update"
		if self.current_chain != None and self.current_chain.chain[-1] == self.current_schema.id:
			print "**Chain exists and executed**"
			if self.ws.satisfies(self.current_schema.postconditions):
				self.current_chain.successes +=1
				print "Chain executed succesfully %i times out of "%self.current_chain.successes, self.current_chain.activations
				self.current_chain = None
			else:
				print "Chain unsuccessfull: ",self.current_chain.successes, self.current_chain.activations
		self.remove_transitory_observations(wsc)
		successful = self.current_schema.update(wsc)
		print "Schema update @ update:",successful
		if(self.current_schema.generalised):
			self.total_generalised_schema_executions += 1
			if(successful):
				self.successful_generalised_schema_executions += 1
		else:
			self.generaliser.assimilate(self.current_schema, self.schemas)
		occurrences = new_state.intersection(self.current_schema.postconditions)
		for o in occurrences.state:
			self.observation_occurred(o)
		last_action = SyntheticObservation()
		last_action.schema = self.current_schema
		last_action.successful = successful
		last_action.sensor_id = -1
		if (prev_state == None):
			return 1
		sub = False
		if ( (prev_state.type_subset(new_state)) and (len(new_state.state) < len(prev_state.state)) ):
			sub = True
		complement_prev_new = prev_state.complement(new_state, False)
		if (complement_prev_new == None or prev_state.equivalents(new_state) ):
			return 2
		if (complement_prev_new != None and not successful and not sub):
			self.remove_transitory_observations(prev_state)
			self.remove_transitory_observations(new_state)
			prev_copy = prev_state.copy()
			self.remove_ignored_preconditions(prev_copy)
			found = self.get_schema(prev_copy, self.current_schema.action, new_state)
			if (found == None):
				found = Schema(self)
				found.preconditions = prev_copy.copy()
				if (self.current_schema.action != None):
					found.action = self.current_schema.action.copy()
				found.postconditions = new_state.copy()
				schema_exists = False
				for s in self.schemas:
					if (s.satisfies(found.preconditions, None, found.postconditions)):
						schema_exists = True
				if (not schema_exists):
					self.add_schema(found)
					self.generaliser.assimilate(found, self.schemas)
			self.current_schema = None; return 3
		self.current_schema = None; return 4


	def get_excited_schemas(self, state):
		if (state == None):
			state = self.ws
		pairs = self.get_excited_schema_pairs(state)
		excited_schemas = []
		for p in pairs:
			excited_schemas.append(p.first)
		return excited_schemas

	def get_excite_all(self, state):
		if (state == None):
			state = self.ws
		pairs = self.get_excited_schema_pairs(state);
		excitation = []
		for p in pairs:
			excitation.append(p.second)
		return excitation

	def get_excited_schema(self, state):
		if (state == None):
			state = self.ws
		excited_schemas = self.get_excited_schema_pairs(state)
		most_excited = excited_schemas[0].first
		return most_excited

	def get_excite(self, s, state):
		excitation = self.excitation_calculator.get_excitation(s, state)
		return excitation

	def get_excited_schema_pairs(self, state):
		if(state == None):
			state = self.get_current_ws()
		excited_schemas = []
		for s in self.schemas:
			excitation = self.excitation_calculator.get_excitation(s, state)
			if excitation > 0:
				p = Pair(s, excitation); excited_schemas.append(p)
		newlist = sorted(excited_schemas, key=lambda k: k.second, reverse=True)
		return newlist


	def execute_excited_schema(self, state):
		if(state == None):
			state = self.ws
		excited_schemas = self.get_excited_schema_pairs(state)
		most_excited = excited_schemas[0].first
		excitation = excited_schemas[0].second
		self.execute(most_excited)
		return excitation


	def get_excited_agent(self, ws):
		wsc = ws.copy(); highest = 0; top =0; excited_schemas = []; excitations = {}
		self.remove_ignored_preconditions(wsc)

		for s in self.schemas:
			exc = self.excitation_calculator.get_excitation(s, wsc)
			pair = Pair(s, exc)
			excited_schemas.append(pair); excitations[s.id] = exc
		excited_schemas = sorted(excited_schemas, key=lambda excited_schemas:excited_schemas.second, reverse=True)
		top = excited_schemas[0].first.id; top_checked = False
		excited_chains = []
		for chainx in self.chains:
			ex = 0
			if self.schemas[chainx.chain[0]].preconditions.equivalents(wsc):
				print "*********ID: ",chainx.chain[0], " satisfies WS************"
			else:
				print "*********ID: ",chainx.chain[0], " NOT satisfies WS*************"
				ex = 0; excited_chains.append(Pair(chainx, ex)); continue
			for C in chainx.chain:
				if (top!=C and not top_checked):
					top_checked = True
					continue
				exm = excitations[C]; ex +=exm
			ex = ex * len(chainx.chain)
			ex = ex*(1+ chainx.successes) /(1+ chainx.activations)
			excited_chains.append(Pair(chainx, ex))
		excited_chains= sorted(excited_chains, key=lambda excited_chains:excited_chains.second, reverse=True)
		#print "Most Exciteds: ", len(excited_chains), len(excited_schemas)
		if len(excited_chains) > 0 and (excited_chains[0].second >= excited_schemas[0].second):
			return excited_chains
		else:
			return excited_schemas

	def execute_excited_agent(self, ws):
		if ws == None:
			agent = self.get_excited_agent(self.ws)
		else:
			agent = self.get_excited_agent(ws)
		if str(type(agent[0].first)) == "<class 'Schema.Schema'>":
			print "Executing Schema: ", agent[0].first.id
			s = self.get_schema_from_id(agent[0].first.id)
			self.execute(s, False)
		elif str(type(agent[0].first)) == "<class 'chains.Chains'>":
			print "Executing chain: ", agent[0].first.chain
			self.current_chain = self.get_chain_from_chain(agent[0].first)
			self.current_chain.activations +=1
			print "Excited chain activations:",self.current_chain.activations
			for c in self.current_chain.chain:
				s = self.get_schema_from_id(c)
				#if self.ws.satisfies(s.postconditions):
				print "Executing chain schema: ", s.id
				self.execute(s)
				if c != self.current_chain.chain[-1]:
					self.emit("update_state")
		else:
			print "Invalid agent found or no excited agent found"


	def execute(self, s, solve = True):
		ws_minus_ignored = self.ws.copy()
		self.remove_ignored_preconditions(ws_minus_ignored)
		if s.generalised:
			s.set_vars_from_state(ws_minus_ignored)
		self.current_schema = s
		if ws_minus_ignored.satisfies(self.current_schema.preconditions):
			print "Current state satisfies preconditions"
			self.current_schema.execute()
			return 1
		elif (ws_minus_ignored.satisfies(self.current_schema.preconditions) and solve):
			print "Acheiving goal in execute"
			self.achieve_goal(self.current_schema.postconditions.get_predictions())
			return 2
		elif (not solve):
			print "Executing schema no %i without state check"%self.current_schema.id
			self.current_schema.execute()
			return 3
		return 4

	def get_average_excitement(self, state):
		if(state == None):
			state = self.ws
		total_excitation = 0
		excited_schemas = self.get_excited_schema_pairs(state)
		for p in excited_schemas:
			total_excitation += p.second
		return total_excitation / self.get_total_schemas()

	def generalise(self, s):
		res = self.generaliser.assimilate(s, self.schemas)
		return res

	def take_action(self, a):
		self.current_schema = self.get_or_create_schema(self.ws, a, WorldState(), True)
		if(self.current_schema.get_probability() < 0.8 and self.current_schema.activations > 100 and not self.current_schema.is_synthetic() and self.last_action != None):
			self.ws.add_observation(self.last_action)
			self.current_schema = self.get_or_create_schema(self.ws, WorldState(), True)
		predicted_world_state = self.current_schema.get_predictions()
		self.current_schema.execute()



	def execute_this_schema(self, this_schema):
		self.execute(this_schema)
		return True

	def execute_id(self, id):
		self.current_schema = self.schemas[id]
		self.current_schema.execute()


	def achieve_target (self, tar, exclu):
		L = []; highest = 0; match = 0; idno = None
		print "Traget received:", tar.to_string()
		for m in range(0, len(self.schemas)):
			if m == exclu:
				continue
			sc = self.get_schema_from_id(m); match = 0;
			#print "Length:"
			#print "ID: %i"%m,(sc.postconditions.equivalents(tar))
			if ((not sc.generalised) and (sc.postconditions.equivalents(tar))):
				L.append(sc.id)
				for o in tar.state:
					for o2 in sc.postconditions.state:
						if (type(o) == type(o2)):
							prop2 = o2.get_properties()
							prop = o.get_concrete_properties()
							for p in prop.keys():
								v2 = prop2[p]
								v1 = prop[p]
								if (v2 != None and  v1 == v2):
									match += 1
				if (match > highest):
					highest = match; idno = sc.id
				L.append(match); L.append(highest); L.append(idno);
		n = self.get_schema_from_id(idno)
		print "Solving target by schema: ", n.id
		n.execute()
		return idno

	def achieve_goal(self, target_state, excluded = None, resolving_target = False):
		wsc = self.ws.copy(); self.remove_ignored_preconditions(wsc)
		sequence = self.find_path2(wsc, target_state, excluded, resolving_target)
		if(len(sequence) == 0):
			return False
		for i in range(0, len(sequence)):
			s = sequence[i]
			if (self.schemas[s].generalised and not resolving_target):
				wsc = self.ws.copy()
				self.remove_ignored_preconditions(wsc)
				self.schemas[s].set_vars_from_state(wsc)
			"""if (not self.ws.satisfies(self.schemas[s].preconditions)):
				return self.achieve_goal(target_state)"""
			self.schemas[s].execute()
		return True


	def execute_sequence_step(self, sequence, target_state):
		if (len(sequence.state) == 0):
			return sequence.copy()
		s = sequence[0]
		if (self.schemas[s].generalised):
			self.remove_ignored_preconditions(self.ws)
			self.schemas[s].set_vars_from_state(self.ws)
		if (not self.ws.satisfies(self.schemas[s].preconditions)):
			target = target_state.copy()
			return self.find_path(self.ws, target, [], False)
		self.schemas[s].execute();
		remaining_sequence = sequence.copy()
		remaining_sequence.remove(s)
		return remaining_sequence


	def find_path(self, state, tar, exclude, resolve = False):
		#PSchema.debug(1, "Created new schema: %d"%5,"general")
		destination = -1; pathschemas = [];
		pathschemas = list(self.schemas)
		distances = {}; sequence = []
		for i in range(0, len(pathschemas)):
			if(pathschemas[i].generalised and not resolve):
				self.remove_ignored_preconditions(state)
				pathschemas[i].set_vars_from_state(state)
			if (state.satisfies(pathschemas[i].preconditions)):
				distances[i] = 0
			else:
				distances[i] = -1
		previous = {}; q = {}
		for i in range(0, len(pathschemas)):
			q[i] = pathschemas[i].copy()
			previous[i] = -1
		#for ex in exclude:
		if len(exclude)> 0:
			q[exclude] = None
		q_length = len(pathschemas); u = -1; u_p = None
		target = tar.copy()
		while(q_length > 0):
			#print "*******************Attempt: %i****************** "%q_length
			shortest_distance = -1
			for i in range(0, len(pathschemas)):
				if (distances[i] == -1 ):
					continue
				if ((distances[i] < shortest_distance or shortest_distance == -1) and q[i] != None):
					shortest_distance = distances[i]
					#print "Distance: ",distances[i], shortest_distance, i
					u = i
					u_p = q[i].copy()
			#print "first distance:", u , u_p.id
			if (shortest_distance == -1):
				break
			q[u] = None
			q_length -= 1
			if (pathschemas[u].generalised and not resolve):
				self.remove_ignored_preconditions(target)
				pathschemas[u].set_vars_from_state(target)
			if (pathschemas[u].postconditions.satisfies(target)):
				destination = u
				break
			for i in range(0, len(pathschemas)):
				if (q[i] == None):
					continue
				if (q[i].generalised and not resolve):
					self.remove_ignored_preconditions(u_p.postconditions)
					q[i].set_vars_from_state(u_p.postconditions)
				if (u_p.postconditions.satisfies(q[i].preconditions)):
					neighbour_distance = 0.001 + 1 - u_p.postconditions.get_probability()
				else:
					continue
				alt = shortest_distance + neighbour_distance
				if (alt < distances[i] or distances[i] == -1):
					distances[i] =alt
					previous[i] = u
		if (destination == -1):
			#print "No path found for:"
			return []
		n = destination
		while (n != -1):
			sequence = [n] +sequence
			n = previous[n]
		if len(sequence) > 1:
			self.add_chain(sequence)
		#print "Found Sequence:", sequence
		#print "PostXXX:",self.get_schema_from_id(3).postconditions.to_string()
		return sequence


	def find_path2(self,state, tar, exclude, resolve = False):
		#PSchema.debug(1, "Created new schema: %d"%5,"general")
		destination = -1; pathschemas = []
		pathschemas = list(self.schemas)
		distances = {}; sequence = []; start = []
		for i in range(0, len(pathschemas)):
			if(pathschemas[i].generalised and not resolve):
				self.remove_ignored_preconditions(state)
				pathschemas[i].set_vars_from_state(state)
			if (state.satisfies(pathschemas[i].preconditions)):
				distances[i] = 0;
				start.append(pathschemas[i].copy())
			else:
				distances[i] = -1
		previous = {}; q = {}
		for i in range(0, len(pathschemas)):
			q[i] = pathschemas[i].copy()
			previous[i] = -1
		#for ex in exclude:
		q[exclude] = None
		q_length = len(pathschemas); u = -1; u_p = None
		target = tar.copy(); self.remove_ignored_preconditions(target)
		for i in range(0, len(start)):
			if(start[i].generalised and not resolve):
				start[i].set_vars_from_state(state)
			if start[i].postconditions.satisfies(target):
				return [start[i].id]
			else:
				for j in range(0, len(pathschemas)):
					if start[i].id == pathschemas[j].id:
						continue
					if pathschemas[j].generalised:
						pathschemas[j].set_vars_from_state(target)
					if pathschemas[j].preconditions.satisfies(self.remove_ignored_preconditions(start[i].postconditions)):
						if pathschemas[j].postconditions.satisfies(target):
							#print "Thats a Hit", start[i].id, pathschemas[j].id
							sequence = [start[i].id, pathschemas[j].id]
							self.add_chain(sequence)
							return sequence
		#print "No path found"
		return []



	def printf(self):
		for schema in self.schemas:
			print schema.to_string()


	def print_xml(self):
		print self.to_xml()

	def to_xml(self):
		builder = ""
		builder += "<?xml version='1.0'?>\n"
		builder += "<pschema>\n"
		for schema in self.schemas:
			builder += schema.to_xml()
		builder += "<associations>\n"
		for p in self.associations.keys():
			builder += "<pair occurrences='%d'>\n"%self.associations[p]
			builder += p.first.to_xml()
			builder += p.second.to_xml()
			builder += "</pair>\n"
		builder += "</associations>\n"
		builder += "<generalised_associations>\n"
		for p in self.generalised_associations.keys():
			builder += "<pair occurrences='%d'>\n"%self.generalised_associations[p]
			builder += p.first.to_xml()
			builder += p.second.to_xml()
			builder += "</pair>\n"
		builder +="</generalised_associations>\n"
		builder +="</pschema>\n"
		return builder

	def load(self, filename):
		tree = ET.parse(filename)
		if (tree == None):
			PSchema.debug(1, "File not found",filename)
			return 1;
		root = tree.getroot()
		if root == None:
			PSchema.debug(1, "Invalid XML :",filename)
			del root
			return 2
		self.parse_node(root)
		highest_id = 0
		for s in self.schemas:
			if (s.id > highest_id):
				highest_id = int(s.id)
		self.next_id = highest_id + 1;
		del root
		return 3


	def parse_node(self, root):
		has_sub_components = False
		for child in root.iter():
			if child.tag == "schema":
				self.loading_schema = Schema(self)
				for k in child.attrib.keys():
						if k =="id":
							self.loading_schema.id = int(child.attrib[k])
						if k =="activations":
							self.loading_schema.activations = float(child.attrib[k])
				self.schemas.append(self.loading_schema)
			if (child.tag=="preconditions" or child.tag == "postconditions" or child.tag == "associated_observations"):
				loading_state_type = child.tag
			if child.tag == "observation":
				o = self.parse_observation(child)
				o.parse_node(child)
				if o.is_generalised():
					self.loading_schema.generalised = True
				if (loading_state_type=="preconditions"):
					self.loading_schema.add_precondition(o)
				elif (loading_state_type == "postconditions"):
					self.loading_schema.add_postcondition(o)
				elif (loading_state_type == "associated_observations"):
					self.loading_schema.add_associated_observation(o)
			if child.tag== "action":
				act = ""
				for k in child.attrib.keys():
					if k =="type":
						act = child.attrib[k]
				if (act != "target"):
					module = __import__(act)
					class_ = getattr(module,act)
					action = class_()
					action.parse_node(child)
					self.loading_schema.action = action
					self.emit("connect_action", action, act)
					has_sub_components = True
				elif (act =="target"):
					action = TargetAction(self)
					action.parse_node(child)
					target = WorldState()
					for grand in child.iter():
						if grand.tag =="observation":
							o2 = self.parse_observation(grand)
							o2.parse_node(child)
							target.add_observation(o2)
					action.target = target
					self.loading_schema.action = action
					loading_state_type = None
					has_sub_components = True
			if (child.tag == "associations" or child.tag == "generalised_associations"):
				has_sub_components = True
				for k in child.iter():
					if(k.tag == "pair"):
						occurrences = 0
						o1 = o2 = None
						for k1 in k.attrib.keys():
							value = k.attrib[k1]
							if (k1 == "occurrences"):
								occurrences = int(value)
						for k3 in k.iter():
							if(k3.tag == "observation"):
								if(o1 == None):
									o1 = self.parse_observation(k3)
									o1.parse_node(k3)
								else:
									o2 = self.parse_observation(k3)
									o2.parse_node(k3)

						if (o1 != None and o2 != None):
							pair = Pair(o1, o2)
							if(child.tag == "associations"):
								self.associations.set(pair, occurrences)
							elif (child.tag == "generalised_associations"):
								self.generalised_associations[pair] = occurrences





	def parse_observation(self, node):
		for k in node.attrib.keys():
			if k =="type":
				ob = node.attrib[k]
				module = __import__(ob)
				class_ = getattr(module,ob)
				observation = class_()
		return observation

	def save( self, filename):
		fo = open(filename, "wb")
		fo.write(self.to_xml())
		fo.close()

	def get_total_schemas(self):
		return len(self.schemas)


	def set_generaliser(self, gen):
		self.generaliser = gen


	def set_excitation_calculator(self, ec):
		self.excitation_calculator = ec


	def observation_occurrences(self, o):
		if (self.observations.has_key(o.hash()) and self.observations[o.hash()] > 0):
			return self.observations[o.hash()]
		else:
			return 0


	def associate_observations(self, po, ao):
		if(po.equals(ao)):
			return
		pair = Pair(po, ao)
		if (self.associations.has_key(pair) and self.associations[pair] > 0):
			self.associations[pair] = self.associations[pair] + 1
		else:
			ga_pair = self.get_generalised_association(po, ao)
			if (ga_pair != None):
				self.generalised_associations[ga_pair] = self.generalised_associations[pair] + 1
				return
			self.generaliser.assimilate_association[pair] = self.associations
			self.associations[pair] = 1


	def add_generalised_associations(self, p):
		self.generalised_associations[p] = 1


	def get_generalised_association(self, po, ao):
		for ga_pair in self.generalised_associations.keys():
			ga = ga_pair.first
			ao2 = ga_pair.second
			if(type(ga) != type(po) or not ao.equals(ao2)):
				continue
			gproperties = ga.get_properties()
			properties = po.get_properties()
			variables = {}
			for property in gproperties.keys():
				g = gproperties[property]
				if(variables.has_key(g) and variables[g] == None):
					variables[g] = properties[property]
			for v in variables.keys():
				ga.instantiate_var(v, variables[v])
			if (ga.equals(po)):
				return ga_pair
		return Pair(Observation(), Observation())

	def associated_observation_occurrences(self, po, ao):
		pair = Pair(po, ao)
		if (self.associations.has_key(pair) and self.associations[pair] > 0):
			return self.associations[pair]
		else:
			gp = self.get_generalised_association(po, ao)
			if (gp != None):
				return self.generalised_associations[pair]
			else:
				return 0
	def observation_occurred(self, o):
		if (self.observations.has_key(o.hash()) and self.observations[o.hash()] > 0):
			self.observations[o.hash()] = self.observations[o.hash()] + 1
		else:
			self.observations[o.hash()] =  1


	def get_associations(self, o):
		aslist = []
		for p in self.associations.keys():
			if(p.first.equals(o)):
				aslist.append(p.second)
		for p in self.generalised_associations.keys():
			ga = p.first
			gproperties = ga.get_properties()
			properties = o.get_concrete_properties()
			variables = {}
			for property in gproperties.keys():
				g = gproperties[property]
				if(variables.has_key(g) and variables[g] == None):
					variables[g] = properties[property]
			for v in variables.keys():
				ga.instantiate_var(v, variables[v])
			if (ga.equals(o)):
				aslist.append(p.second)
		return aslist


	def get_chains_containing(self, id):
		containers = [[]]
		for i in range(0, len(self.chains)):
			chain = list(self.chains[i])
			if (id in chain):
				containers.append(list(chain))
		return containers;


debug_level = 0
debug_filter = None;
print_changes = False;

def debug(self, level, message, filter = "general"):
	if (debug_level >= level and (debug_filter == filter or debug_filter == None)):
		print("[%d - %s] %s\n",level, filter, message)