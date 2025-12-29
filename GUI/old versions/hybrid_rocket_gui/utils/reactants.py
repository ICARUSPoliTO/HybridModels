# utils/reactants.py

try:
    import CoolProp.CoolProp as cp
    COOLPROP_AVAILABLE = True
except ImportError:
    COOLPROP_AVAILABLE = False
    print("Warning: CoolProp not available. Using fallback oxidizer list.")

from config import EASY_CEA_OX_LIST, EASY_CEA_FUEL_LIST, FALLBACK_COOLPROP_FLUIDS


class ReactantManager:
    def __init__(self):
        self.cea_reactants = []
        self.easy_cea_ox_list = EASY_CEA_OX_LIST
        self.easy_cea_fuel_list = EASY_CEA_FUEL_LIST
        self.coolprop_available = COOLPROP_AVAILABLE
        
        self._load_cea_reactants()
        self._load_coolprop_fluids()
    
    def _load_cea_reactants(self):
        try:
            with open("CEA_reactants.txt", "r", encoding="utf-8") as f:
                self.cea_reactants = [line.strip() for line in f.readlines() if line.strip()]
            self.cea_reactants.sort()
        except FileNotFoundError:
            print("Warning: CEA_reactants.txt not found. Using empty reactant list.")
            self.cea_reactants = []
    
    def _load_coolprop_fluids(self):
        if self.coolprop_available:
            self.coolprop_fluids = cp.FluidsList()
        else:
            self.coolprop_fluids = FALLBACK_COOLPROP_FLUIDS
    
    def get_cea_reactants(self):
        return self.cea_reactants
    
    def get_oxidizer_list(self):
        return self.easy_cea_ox_list
    
    def get_fuel_list(self):
        return self.easy_cea_fuel_list
    
    def get_coolprop_fluids(self):
        return self.coolprop_fluids