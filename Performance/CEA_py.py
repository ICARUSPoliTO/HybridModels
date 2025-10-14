## Code to write CEA input and run a rocket problem in CEA with a
# modified output to read and write in the map (if check is passed).
# Special thanks to Prof. Filippo Masseni for providing the CEA source code and modifying it's output.
# Due to issues related to the Fortran code, caused by bad reading of the natives input file we will
# use RocketCEA package. Documentation at: https://rocketcea.readthedocs.io/en/latest/quickstart.html
import os
from rocketcea.cea_obj import CEA_Obj, add_new_fuel, add_new_oxidizer


def runCEA(pc, MR, eps, oxCEA, fuelCEA):
    # Fuel(s)
    newfuel = ""
    for i in range(len(fuelCEA["Fuels"])):
        if fuelCEA["Temperature [K]"][i] != "" and fuelCEA["Specific Enthalpy [kj/mol]"][i] != "":

            newfuel += (f"fuel {fuelCEA['Fuels'][i]}    {fuelCEA['Exploded Formula'][i]}"
                        f"    wt%=    {fuelCEA['Weight fraction'][i]}"
                        f"    t,k= {fuelCEA['Temperature [K]'][i]}"
                        f"    h,cal= {fuelCEA['Specific Enthalpy [kj/mol]'][i] * 239.0057}\n")

        elif fuelCEA["Temperature [K]"][i] != "" and fuelCEA["Specific Enthalpy [kj/mol]"][i] == "":

            newfuel += (
                f"fuel {fuelCEA['Fuels'][i]}    {fuelCEA['Exploded Formula'][i]}"
                f"    wt%=    {fuelCEA['Weight fraction'][i]}"
                f"    t,k= {fuelCEA['Temperature [K]'][i]}\n")

        elif fuelCEA["Temperature [K]"][i] == "" and fuelCEA["Specific Enthalpy [kj/mol]"][i] != "":

            newfuel += (
                f"fuel {fuelCEA['Fuels'][i]}    {fuelCEA['Exploded Formula'][i]}"
                f"    wt%=    {fuelCEA['Weight fraction'][i]}"
                f"    h,cal= {fuelCEA['Specific Enthalpy [kj/mol]'][i] * 239.0057}\n")
        else:
            newfuel += (
                f"fuel {fuelCEA['Fuels'][i]}    {fuelCEA['Exploded Formula'][i]}"
                f"    wt%=    {fuelCEA['Weight fraction'][i]}\n")

    # Oxidizer
    if oxCEA["Temperature [K]"] != "" and oxCEA["Specific Enthalpy [kj/mol]"] != "":

        newoxid = (f"oxid {oxCEA['OxidizerCEA']}    {oxCEA['Exploded Formula']}"
                   f"    wt%=    {oxCEA['Weight fraction']}"
                   f"    t,k= {oxCEA['Temperature [K]']}"
                   f"    h,cal= {oxCEA['Specific Enthalpy [kj/mol]'] * 239.0057}\n")

    elif oxCEA["Temperature [K]"] != "" and oxCEA["Specific Enthalpy [kj/mol]"] == "":

        newoxid = (f"oxid {oxCEA['OxidizerCEA']}    {oxCEA['Exploded Formula']}"
                   f"    wt%=    {oxCEA['Weight fraction']}"
                   f"    t,k= {oxCEA['Temperature [K]']}\n")

    elif oxCEA["Temperature [K]"] == "" and oxCEA["Specific Enthalpy [kj/mol]"] != "":

        newoxid = (f"oxid {oxCEA['OxidizerCEA']}    {oxCEA['Exploded Formula']}"
                   f"    wt%=     {oxCEA['Weight fraction']}"
                   f"    h,cal= {oxCEA['Specific Enthalpy [kj/mol]'] * 239.0057}\n")

    else:
        newoxid = (f"oxid {oxCEA['OxidizerCEA']}    {oxCEA['Exploded Formula']}"
                   f"    wt%=    {oxCEA['Weight fraction']}\n")

    add_new_oxidizer('NEWOX', newoxid)
    add_new_fuel('NEWFUEL', newfuel)

    C = CEA_Obj(oxName="NEWOX", fuelName="NEWFUEL",
                useFastLookup=0, makeOutput=0)

    Ivac, cs, Tc, M, g = C.get_IvacCstrTc_ThtMwGam(pc * 14.503773800722e-5, MR, eps)  # pc [psia]


    if Ivac != 0 and cs != 0:

        cs = cs * 0.3048 #[ft/s] -> [m/s]
        Tc = Tc * 5 / 9 #[°R] -> [K]

        cfvac = (Ivac*9.81) / cs

        output_list = [Tc, M, g, cs, cfvac]

    else:
        output_list = []

    return output_list


def writemap(pc, MR, eps, oxCEA, fuelCEA, output_list):

    if output_list != []:
        MAPname = "MAP_" + oxCEA['OxidizerCEA']
        for i in range (len(fuelCEA['Fuels'])):
            MAPname = MAPname + "_" + fuelCEA['Fuels'][i] + fuelCEA['Weight fraction'][i]

        MAPname = MAPname + ".txt"
        MAPname = os.path.join(".", "MAPS", MAPname)

        MAPfile = open(MAPname, "a")

        MAPline = [f"{MR:018.16f}"[:18], f"{pc:018.16f}"[:18], f"{eps:018.16f}"[:18]]
        for element in output_list:
            MAPline.append(f"{element:018.16f}"[:18])

        MAPline = "        ".join(MAPline)
        MAPline = "   " + MAPline
        MAPline = MAPline.ljust(209)

        MAPfile.write(MAPline + "\n")
        MAPfile.close()

## end of file