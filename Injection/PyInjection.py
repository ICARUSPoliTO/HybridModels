import CoolProp.CoolProp as cp
import numpy as np
import matplotlib.pyplot as plt

# This script provides a model for double phase fluid injection system, according to
# "Mass Flow Rate and Isolation Characteristics of Injectors for Use with Self-Pressurizing Oxidizers
# in Hybrid Rockets" - Benjamin S. Waxman, Jonah E. Zimmerman, Brian J. Cantwell
# Stanford University, Stanford, CA 94305
# and
# Gregory G. Zilliac
# NASA Ames Research Center, Mo et Field, CA 94035
#

class Injector(object):
    def __init__(self, fluid):
        if fluid in cp.FluidsList():
            self.fluid = fluid
        else:
            print("Fluid not found")
            print(cp.FluidsList())
            exit('Read the list above and try again!')

    def injection_area(self, D, n):
        # D = 'Hole diameter [m]', n = 'Number of holes'
        self.A = 0.25 * n * np.pi * (D ** 2)

    def massflow(self, p1, p2, T, cD):
        # Isothermal fluid in the line (hypothesis)
        # p1 = Tank pressure[Pa], p2 = Chamber pressure[Pa], T = Tank temperature[K]
        try:
            h1 = cp.PropsSI('H', 'P',p1,'T',T, self.fluid)
        except ValueError:
            h1 = cp.PropsSI('H', 'T', T, 'Q', 0, self.fluid)

        try:
            h2 = cp.PropsSI('H', 'P', p2, 'T', T, self.fluid)
        except ValueError:
            h2 = cp.PropsSI('H', 'T', T, 'Q', 1, self.fluid)

        try:
            d2 = cp.PropsSI('D', 'P',p2,'T',T, self.fluid)
        except ValueError:
            d2 = cp.PropsSI('D', 'T', T, 'Q', 1, self.fluid)

        dSPI = cp.PropsSI('D', 'T',T, 'Q', 0, self.fluid)

        # Vapor pressure
        pV = cp.PropsSI('P','T',T, 'Q', 1, self.fluid)

        if p1 > p2:
            mdot_SPI = cD * np.sqrt(2 * dSPI * (p1 - p2)) #[kg/s*m^2]

            mdot_HEM = cD * d2 * np.sqrt(2 * abs(h1 - h2)) #[kg/s*m^2]
            """
            if pV > p1: # N2O is always gas
                gamma = (cp.PropsSI('CPMASS', 'P', p1, 'T', T, self.fluid)
                         /cp.PropsSI('CVMASS', 'P', p1, 'T', T, self.fluid))
                R = 8314/(cp.PropsSI('MOLARMASS', 'P', p1, 'T', T, self.fluid)/1e-3)

                mdot = cD * p1/np.sqrt(R*T)
                gammone = np.sqrt(gamma * (2 / (gamma + 1)) ** ((gamma + 1) / (gamma - 1)))
                pe_pc_crit = (2 / (gamma + 1)) ** (gamma / (gamma - 1))
                if (p2 / p1) < pe_pc_crit: # Is critical?
                    mdot = mdot * gammone
                else:
                    mdot= mdot * np.sqrt((2 * gamma) * ((p2 / p1) ** (2 / gamma) - (p2 / p1) ** ((gamma + 1) / gamma)) / (gamma - 1))
            """
            if pV > p2: # N2O exits as a mixture
                k = np.sqrt((p1 - p2) / (pV - p2))

                mdot = (k * mdot_SPI / (k + 1) + mdot_HEM / (k + 1)) #[kg/s*m^2]
            else: # N2O is always liquid
                mdot = mdot_SPI #[kg/s*m^2]

            self.mdot = mdot
            # self.mdot_SPI = mdot_SPI * self.A
            # self.mdot_HEM = mdot_HEM * self.A
        else:
            #print('Backflow not possible')
            self.mdot = 0
            self.mdot_SPI = 0
            self.mdot_HEM = 0

if __name__ == '__main__':
    ## Code to verify the injection model and to explain its use
    plt.close('all')

    ox = Injector('NitrousOxide')

    ox.injection_area(0.0127,1)
    pinj= 2e5 #[Pa]
    Ttank = 288  # [K]
    pc = 1e5 #[Pa]
    mdot= np.zeros(np.shape(pinj))
    mdot_SPI= np.zeros(np.shape(pinj))
    mdot_HEM= np.zeros(np.shape(pinj))

    print('M='+str(cp.PropsSI('MOLARMASS', ox.fluid)*1e3))
    ox.massflow(pinj, pc, Ttank, 1)
    mdot = ox.mdot * ox.A

    mfuel = 0.116*(mdot/(0.25*np.pi*(13.4E-3)**2))**0.331

    print(pinj)
    print(mdot)

    #plt.plot(pinj,mdot, label='Dyer')

    #plt.xlabel('Injection pressure [bar]')
    #plt.ylabel('Mass flow [kg/s]')
    #plt.legend()
    #plt.show()

# end of file