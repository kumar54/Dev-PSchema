from Observation import Observation

class SyntheticObservation(Observation):

	def __init__(self):
		Observation.__init__(self)
		self.schema = None
		self.schema_var = None
		self.successful_var = None
		self.successful = False

	
	def equals(self, o2):
		if (type(self) != type(o2)):
			return False;
		so2 = SyntheticObservation(o2)
		if (self.schema == None):
			return False
		return self.schema.equals(o2.schema) and self.successful == o2.successful


	def copy(self):
		so = SyntheticObservation()
		so.schema = self.schema.copy()
		so.successful = self.successful
		so.sensor_id = self.sensor_id
		return so


	def get_properties(self):
		props = {}
		if (self.schema_var != None):
			props["schema"] = self.schema_var
		else:
			props["schema"] = self.schema.id.to_string()
		if (self.successful_var != None):
			props["successful"] =  self.successful_var
		else:
			props["successful"] = self. successful.to_string()
		return props;
	

	def get_concrete_properties(self):
		props = {}
		props["schema"] = self.schema.id.to_string()
		props["successful"] = self.successful.to_string()
		return props


	def set_property_var(self, property, variable):
		if property == "schema":
			self.schema_var = variable
		if property == "successful":
			self.successful_var = variable
