from gi.repository import GObject

class Chains(GObject.Object):

    def __init__(self, chain):
        self.chain = chain
        self.activations = 0
        self.successes = 0
        #print "Pair type:", type(self)

    def equals(self, chain2):
        return self.chain == chain2.chain
