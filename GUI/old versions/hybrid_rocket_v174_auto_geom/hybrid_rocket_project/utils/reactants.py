"""
Reactant Manager

Manages lists of oxidizers and fuels from CEA and CoolProp.
"""

try:
    import CoolProp.CoolProp as cp
    COOLPROP_AVAILABLE = True
except ImportError:
    COOLPROP_AVAILABLE = False
    print("Warning: CoolProp not available. Using fallback oxidizer list.")


class ReactantManager:
    """Manages reactant lists for oxidizers and fuels"""
    
    def __init__(self, cea_file_path: str = "CEA_reactants.txt"):
        self.cea_reactants = []
        self.cea_file_path = cea_file_path
        self.coolprop_available = COOLPROP_AVAILABLE
        
        # Easy lists for common reactants
        self.easy_cea_ox_list = [
            "Air", "CL2", "CL2(L)", "F2", "F2(L)", "H2O2(L)",
            "N2H4(L)", "N2O", "NH4NO3(I)", "O2", "O2(L)",
            "Select other options", "Custom with exploded formula"
        ]
        
        self.easy_cea_fuel_list = [
            "CH4", "CH4(L)", "H2", "H2(L)", "RP-1", "paraffin",
            "Select other options", "Custom with exploded formula"
        ]
        
        # Fallback CoolProp fluids if library not available
        self.fallback_coolprop_fluids = [
            "NitrousOxide", "Oxygen", "Nitrogen", "Water",
            "CarbonDioxide", "Methane", "Hydrogen"
        ]
        
        self._load_cea_reactants()
        self._load_coolprop_fluids()
    
    def _load_cea_reactants(self):
        """Load CEA reactants from file"""
        try:
            with open(self.cea_file_path, "r", encoding="utf-8") as f:
                self.cea_reactants = [line.strip() for line in f.readlines() if line.strip()]
            self.cea_reactants.sort()
            print(f"✓ Loaded {len(self.cea_reactants)} CEA reactants")
        except FileNotFoundError:
            print(f"Warning: {self.cea_file_path} not found. Using empty reactant list.")
            self.cea_reactants = []
    
    def _load_coolprop_fluids(self):
        """Load CoolProp fluids list"""
        if self.coolprop_available:
            try:
                self.coolprop_fluids = cp.FluidsList()
                print(f"✓ CoolProp available with {len(self.coolprop_fluids)} fluids")
            except:
                self.coolprop_fluids = self.fallback_coolprop_fluids
                print("✓ Using fallback CoolProp fluids")
        else:
            self.coolprop_fluids = self.fallback_coolprop_fluids
            print("✓ Using fallback CoolProp fluids (CoolProp not installed)")
    
    def get_cea_reactants(self):
        """Get full list of CEA reactants"""
        return self.cea_reactants
    
    def get_oxidizer_list(self):
        """Get common oxidizer list"""
        return self.easy_cea_ox_list
    
    def get_fuel_list(self):
        """Get common fuel list"""
        return self.easy_cea_fuel_list
    
    def get_coolprop_fluids(self):
        """Get CoolProp fluids list"""
        return self.coolprop_fluids
