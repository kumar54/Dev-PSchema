#import PSchema
from WorldState import WorldState
class NoveltyCalculator(object):

    def __init__(self, mem):
        self.m = mem

    def get_excitation(self, s, ws):
        excitation = 1; path_length = 0; wsc = ws.copy()
        self.m.remove_ignored_preconditions(wsc); pre = s.preconditions
        redundant = s.set_vars_from_state(wsc)
        if wsc.satisfies(s.preconditions):
            path_length = 1
        else:
            target_state = s.get_predictions().copy()
            path= self.m.find_path(wsc, target_state, [], False)
            #print "Found Path for agent: ",s.id, path
            path_length = len(path)
            if (path_length < 1):
                print "No Path found for ",s.id, " @novelty"
                return 0
        if pre !=None:
            if (len(pre.state) >0) and not pre.equivalents(wsc) and not s.generalised:
                print "schema ", s.id, "disquallified @ novelty"
                return 0
        po = s.postconditions
        for o in wsc.state:
            for o2 in po.state:
                oexcitation = o.get_similarity(o2) / (1 + self.m.observation_occurrences(o))
                excitation += oexcitation
        excitation /= (1 + s.activations); excitation *= 1.00/(path_length); excitation *= (1+ s.successes)
        if( len(redundant.state) == 1):
            ws2 = WorldState(); ro = redundant.state[0]; added = False
            for o in wsc.state:
                if (not added and type(o) == type(ro) and not o.equals(ro)):
                    ws2.add_observation(ro); added = True
                else:
                    ws2.add_observation(o)
            if(not added):
                return excitation
            excitation2 = self.get_excite(s, ws2)
            if (excitation2 > excitation):
                return excitation2
            else:
                s.set_vars_from_state(wsc)
            return excitation
        return excitation