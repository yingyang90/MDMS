import os
import pandas as pd
import re
import subprocess
from pathlib import Path


def file_naming():
    # getting name for a control file, which will containg all info
    global filename
    while True:
        try:
            filename_inp: str = Path(input('Please, provide a path to the file that contains every piece of information for running MDMS (it should be already generated):\n'))
            filename = filename_inp
            if filename.exists():
                break
            else:
                print('There is no such file.')
        except BaseException:
            print('Please, provide valid input')


def save_to_file(content, filename):
    # saving to a control file
    with open(filename, 'a') as file:
        file.write(content)


def read_file(filename):
    # reading files
    with open(filename, 'r') as file:
        return file.read()


def file_check(file):
    # checking, if a file exists
    test = file.exists()
    return test


def stop_interface():
    # enforce stopping the entire interface
    global stop_generator
    stop_generator = True


def clearing_control():
    # this function clears control file from what will be inputted with topology_prep run
    # name of temporary file that will store what is important
    filetemp = 'temp.txt'
    # list of parameters that will be stripped out of control file
    parameters = [
        'charge_model',
        'atoms_type',
        'ligands_charges',
        'ligands_multiplicities']
    # writing content of control file without parameters in parameters list to
    # the temporary file
    with open(f"{filename}") as oldfile, open(filetemp, 'w') as newfile:
        for line in oldfile:
            if not any(parameters in line for parameters in parameters):
                newfile.write(line)
    # replacing control file with temporary file
    os.replace(filetemp, filename)


def hydrogen_check():
    # Checking if hydrogens are added to ligands file
    control = read_file(filename)
    ligands = r'ligands\s*=\s*\[(.*)\]'
    ligands_match = re.search(ligands, control)
    # if there are ligands, following clause will be executed
    if ligands_match:
        # taking only ligands entries
        ligands_match = ligands_match.group(1)
        # removing quotes from string
        ligands_string = ligands_match.replace("'", "")
        # removing whitespaces and turning string into a list
        ligands_list = re.sub(r'\s', '', ligands_string).split(',')
        # storing info about how many atoms are in ligands
        atoms_amount = []
        # storing info about how many hydrogen atoms are in ligands
        hydrogens_amount = []
        # following clause will be executed only if there are ligands in the
        # control file
        if ligands_list:
            for ligand in ligands_list:
                # reading 3rd column (pandas numbering - 2nd) from ligand.pdb -
                # if there are no hydrogens in residue names, there are no
                # hydrogens in the whole file
                df = pd.read_csv(f'{ligand}.pdb', header=None, delim_whitespace=True, usecols=[2])
                # getting info how many atoms are in a ligand
                df_len = len(df.iloc[:, 0])
                # storing info in list, which will contain info about all
                # ligands
                atoms_amount.append(df_len)
                # establishing if there are hydrogens in atom names
                hydrogen_match = (df[df.iloc[:, 0].str.match('H')])
                # counting how many hydrogens were in a ligand
                hydrogen_count = len(hydrogen_match.iloc[:, 0])
                # storing info about amount of hydrogens in a list
                hydrogens_amount.append(hydrogen_count)
            stop = False
            for x in range(0, len(ligands_list)):
                if hydrogens_amount[x] == 0:
                    USER_CHOICE_HYDROGENS = (f"Even though there are {atoms_amount[x]} atoms in {ligands_list[x]} ligand, there are no "
                                             f"hydrogen atoms. Please keep in mind that all of the ligands MUST have all the "
                                             f"necessary hydrogen atoms in their structures. If you do not add chemically-"
                                             f"relevant hydrogen atoms to your ligands, your MD simulations will provide "
                                             f"unrealistic insight.\n"
                                             f"Are you sure that {ligands_list[x]} ligand should not have any hydrogen atoms?\n"
                                             f"- press 'y' to continue\n"
                                             f"- press 'n' to stop MDMS run\n")
                    while True:
                        try:
                            user_input_hydrogens = str(
                                input(USER_CHOICE_HYDROGENS).lower())
                            if user_input_hydrogens == 'y':
                                break
                            elif user_input_hydrogens == 'n':
                                stop = True
                                break
                        except BaseException:
                            print('Please, provide valid input')
                    if stop:
                        break
                    else:
                        pass
            if stop:
                stop_interface()


def ligands_parameters():
    # reading control file
    control = read_file(filename)
    # finding ligands residues in prep file
    ligands = r'ligands\s*=\s*\[(.*)\]'
    ligands_match = re.search(ligands, control)
    if ligands_match:
        # taking only ligands entries
        ligands_match = ligands_match.group(1)
        # removing quotes from string
        ligands_string = ligands_match.replace("'", "")
        # removing whitespaces and turning string into a list
        ligands_list = re.sub(r'\s', '', ligands_string).split(',')
        # getting necessary infor for antechamber input
        USER_CHOICE_CHARGE_MODEL = f"\nPlease specify the charge model that you would like to apply to your ligands. If you want" \
            f"to employ RESP charges, you will need to manually modify antechamber input files.\n" \
            f"Please note that AM1-BCC charge model is a recommended choice.\n" \
            f"Following options are available:\n" \
            f"- 'bcc' - AM1-BCC charge model\n" \
            f"- 'mul' - Mulliken charge model\n" \
            f"Please, provide one of the options from available answers (single-quoted words specified above):\n"
        USER_CHOICE_ATOM_TYPES = f"\nPlease, specify which atom types you would like to assign to your ligands.\n" \
            f"Please note that GAFF2 is a recommended choice.\n" \
            f"Following options are available:\n" \
            f"- 'gaff2' - General Amber Force Field, version 2\n" \
            f"- 'gaff' - General Amber Force Field, older version of GAFF2\n" \
        # the whole function will only do something, if ligands_list have
        # anything in it
        if ligands_list:
            # prompting user that he MUSTS have hydrogens already added to the
            # specifying charge model
            while True:
                try:
                    user_input_charge_model = str(
                        input(USER_CHOICE_CHARGE_MODEL).lower())
                    if user_input_charge_model == 'bcc':
                        charge_model = 'bcc'
                        break
                    elif user_input_charge_model == 'mul':
                        charge_model = 'mul'
                        break
                except BaseException:
                    print('The input that you have provided is not valid.')
            save_to_file(f"charge_model = {charge_model}\n", filename)
            # specifying atom types
            while True:
                try:
                    user_input_atom_types = str(
                        input(USER_CHOICE_ATOM_TYPES).lower())
                    if user_input_atom_types == 'gaff':
                        atoms_type = 'gaff'
                        break
                    elif user_input_atom_types == 'gaff2':
                        atoms_type = 'gaff2'
                        break
                except BaseException:
                    print('The input that you have provided is not valid')
            save_to_file(f"atoms_type = {atoms_type}\n", filename)
            # specifying charges and multiplicity for each ligand
            lig_charges = []
            lig_multiplicities = []
            for x in ligands_list:
                # those must be looped on, since each ligand might have different charge and multiplicity
                USER_CHOICE_CHARGE = f"Please, provide the net charge of {x} ligand (integer value):\n"
                while True:
                    # this loop gets info about ligands charges
                    try:
                        # this line already tests if input is integer
                        user_input_charge = int(input(USER_CHOICE_CHARGE))
                        lig_charges.append(user_input_charge)
                        break
                    except BaseException:
                        print("The input that you have provided is not valid")
            # once charges are known and good, they are put into control file
            save_to_file(f"ligands_charges = {lig_charges}\n", filename)
            for x in ligands_list:
                # this loop gets info about ligands multipicities
                USER_CHOICE_MULTIPLICITY = f"\nPlease, provide multiplicity of {x} ligand (positive integer value):\n"
                while True:
                    try:
                        # multiplicity must be integer but also must be
                        # positive
                        user_input_multiplicity = int(
                            input(USER_CHOICE_MULTIPLICITY))
                        if user_input_multiplicity < 1:
                            raise Exception
                        lig_multiplicities.append(user_input_multiplicity)
                        break
                    except BaseException:
                        print("The input that you have provided is not valid")
            # once multiplicity is good, its saved into control file
            save_to_file(f"ligands_multiplicities = {lig_multiplicities}\n", filename)


def antechamber_parmchk_input():
    # finding ligands residues in control file
    control = read_file(filename)
    ligands = r'ligands\s*=\s*\[(.*)\]'
    ligands_match = re.search(ligands, control)
    if ligands_match:
        # taking only ligands entries
        ligands_match = ligands_match.group(1)
        # removing quotes from string
        ligands_string = ligands_match.replace("'", "")
        # removing whitespaces and turning string into a list
        ligands_list = re.sub(r'\s', '', ligands_string).split(',')
        # getting charge_model info
        charge_model = r'charge_model\s*=\s*([a-z]*[A-Z]*[1-9]*)'
        charge_model_match = re.search(charge_model, control).group(1)
        # getting atom_types info
        atoms_type = r'atoms_type\s*=\s*([a-z]*[A-Z]*[1-9]*)'
        atoms_type_match = re.search(atoms_type, control).group(1)
        # finding ligands' charges in control file
        ligands_charges = r'ligands_charges\s*=\s*\[(.*)\]'
        ligands_charges_match = re.search(ligands_charges, control).group(1)
        # removing whitespaces and turning to a list
        ligands_charges_list = re.sub(
            r'\s', '', ligands_charges_match).split(',')
        # changing individual entries from string to integers
        for x in range(0, len(ligands_charges_list)):
            ligands_charges_list[x] = int(ligands_charges_list[x])
        # finding ligands multiplicities in control file
        ligands_multiplicities = r'ligands_multiplicities\s*=\s*\[(.*)\]'
        ligands_multiplicities_match = re.search(
            ligands_multiplicities, control).group(1)
        # removing whitespaces and turning to a list
        ligands_multiplicities_list = re.sub(
            r'\s', '', ligands_multiplicities_match).split(',')
        # changing individual entries from string to integers
        for x in range(0, len(ligands_multiplicities_list)):
            ligands_multiplicities_list[x] = int(
                ligands_multiplicities_list[x])
        # prior to to antechamber and parmchk execution, check ligands pdb with
        # pdb4amber
        for x in range(0, len(ligands_list)):
            # copying original ligand PDB file - output from pdb4amber will be
            # supplied to antechamber and parmchk
            ligand_copy = f"cp {ligands_list[x]}.pdb {ligands_list[x]}_original.pdb"
            subprocess.run([f"{ligand_copy}"], shell=True)
            # input for pdb4amber
            pdb4amber_input = f"pdb4amber -i {ligands_list[x]}_original.pdb -o {ligands_list[x]}.pdb "
            # running pdb4amber (both original and remade files are retained
            # but later on remade ligands will be operated on
            subprocess.run([f"{pdb4amber_input}"], shell=True)
        # creating antechamber and parmchk inputs
        for x in range(0, len(ligands_list)):
            # input for antechamber
            antechamber_input = f"antechamber -fi pdb -fo mol2 -i {ligands_list[x]}.pdb -o {ligands_list[x]}.mol2 -at {atoms_type_match} -c {charge_model_match} -pf y -nc {ligands_charges_list[x]} -m {ligands_multiplicities_list[x]}"
            # running antechamber
            subprocess.run([f"{antechamber_input}"], shell=True)
            # checking if mol2 was succesfully created
            mol2_path = Path(f'{ligands_list[x]}.mol2')
            if file_check(mol2_path) == False:
                # if mol2 was not created, loop stops and user is returned to
                # menu
                print(f"\nAntechamber has failed to determine atomic charges for {ligands_list[x]} ligand. Please, have a look"
                      f" at output files for more info.\n")
                break
            # input for parmchk
            parmchk_input = f"parmchk2 -i {ligands_list[x]}.mol2 -o {ligands_list[x]}.frcmod -f mol2 -s {atoms_type_match}"
            # running parmchk
            subprocess.run([f"{parmchk_input}"], shell=True)
            # checking if frcmod was successfully created
            frcmod_path = Path(f'{ligands_list[x]}.frcmod')
            if file_check(frcmod_path) == False:
                # if frcmod was not created, loop stops and user is returned to
                # menu
                print(f"\nParmchk has failed to run correctly for {ligands_list[x]} ligand. Please, check validity of"
                      f" {ligands_list[x]}.mol2 file.\n")
                break


def pdb_process():
    # This function strips original PDB of anything apart from protein, checks its validity with pdb4amber and create
    # PDB complex of protein and ligands, which will be passed onto tleap
    # this will inform user what is being done
    print('\nRight now your PDB will be processed in order to ensure a proper working with Amber software. If there'
          ' are any missing atoms in amino acids, they will be automatically added with pdb4amber program.\n')
    # reading pdb from control file
    control = read_file(filename)
    structure = r'pdb\s*=\s*(.*)'
    structure_match = re.search(structure, control).group(1)
    # stripping of extension from structure - this way it will be easier to
    # get proper names, i.e. 4zaf_old.pdb
    structure_match_splitted = structure_match.split('.')[0]
    # copying original PDB file so it will be retained after files operations
    struc_copy = f"cp {structure_match} {structure_match_splitted}_original.pdb"
    subprocess.run([f"{struc_copy}"], shell=True)
    # input for pdb4amber - ligands are removed
    pdb4amber_input = f"pdb4amber -i {structure_match_splitted}_original.pdb --add-missing-atoms -p -o {structure_match_splitted}_no_lig.pdb"
    # running pdb4amber (both original and remade files are retained but later
    # on remade ligands will be operated on
    subprocess.run([f"{pdb4amber_input}"], shell=True)
    # finding ligands residues in control file
    ligands = r'ligands\s*=\s*\[(.*)\]'
    ligands_match = re.search(ligands, control)
    # finding crystal waters residue in control file
    waters = r'waters\s*=\s*\[(.*)\]'
    waters_match = re.search(waters, control)
    # finding metal residues in control file
    metals = r'metals\s*=\s*\[(.*)\]'
    metals_match = re.search(metals, control)
    # creating list storing filenames that will create the whole complex
    full_files = []
    # protein without any ligands
    struc_no_lig = f"{structure_match_splitted}_no_lig.pdb"
    # protein filename appended
    full_files.append(struc_no_lig)
    if waters_match:
        # taking only residues names
        waters_match = waters_match.group(1)
        # removing quotes from string
        waters_string = waters_match.replace("'", "")
        # removing whitespaces and turning string into a list
        waters_list = re.sub(r'\s', '', waters_string).split(',')
        # creating a list that will store waters filenames
        waters_files = []
        # appending waters filenames to the list
        for water in waters_list:
            waters_files.append(f"{water}.pdb")
        # appending waters to files that will create final complex
        for water in waters_files:
            full_files.append(water)
    if metals_match:
        # taking only ligands entries
        metals_match = metals_match.group(1)
        # removing quotes from string
        metals_string = metals_match.replace("'", "")
        # removing whitespaces and turning string into a list
        metals_list = re.sub(r'\s', '', metals_string).split(',')
        # creating a list that will store ligands filenames
        metals_files = []
        # appending ligands filenames to the list
        for metal in metals_list:
            metals_files.append(f"{metal}.pdb")
        # appending ligands filenames
        for metal in metals_files:
            full_files.append(metal)
    if ligands_match:
        # taking only ligands entries
        ligands_match = ligands_match.group(1)
        # removing quotes from string
        ligands_string = ligands_match.replace("'", "")
        # removing whitespaces and turning string into a list
        ligands_list = re.sub(r'\s', '', ligands_string).split(',')
        # creating a list that will store ligands filenames
        ligands_files = []
        # appending ligands filenames to the list
        for ligand in ligands_list:
            ligands_files.append(f"{ligand}.pdb")
        # appending ligands filenames
        for ligand in ligands_files:
            full_files.append(ligand)
    complex_raw = f"{structure_match_splitted}_raw.pdb"
    # using context manager to concatenate protein and ligands together
    print(full_files)
    with open(complex_raw, 'w') as outfile:
        # iterating over each file in full_files list
        for fname in full_files:
            # opening each file and writing it to outfile
            with open(fname) as infile:
                outfile.write(infile.read())
    # name of the pdb file that will be an input for tleap
    complex = f"{structure_match_splitted}_full.pdb"
    # processing protein-ligand complex pdb file with pdb4amber
    pdb4amber_input_complex = f"pdb4amber -i {complex_raw} -o {complex}"
    # running pdb4amber
    subprocess.run([f"{pdb4amber_input_complex}"], shell=True)


def tleap_input():
    tleap_file = Path('tleap.in')
    # if input file already exists, remove it
    if tleap_file.exists():
        os.remove(tleap_file)
    # reading pdb from control file
    control = read_file(filename)
    structure = r'pdb\s*=\s*(.*)'
    structure_match = re.search(structure, control).group(1)
    # stripping of extension from structure - this way it will be easier to
    # get proper names, i.e. 4zaf_old.pdb
    structure_match_splitted = structure_match.split('.')[0]
    # name of the pdb file that will be an input for tleap
    complex = f"{structure_match_splitted}_full.pdb"
    # options for tleap
    # protein force field
    USER_CHOICE_PROTEIN_FF = (
        f"\nPlease, choose force field which will be used for the protein during your simulations.\n"
        f"Please, note that the recommended choice is ff14SB.\n"
        f"The following options are available:\n"
        f"- 'ff14sb'\n"
        f"- 'ff15ipq'\n"
        f"- 'fb15'\n"
        f"- 'ff03'\n"
        f"- 'ff03ua'\n"
        f"Please, provide your choice:\n"
    )
    while True:
        try:
            # user chooses which protein force field to use
            user_input_protein_ff = str(input(USER_CHOICE_PROTEIN_FF).lower())
            if user_input_protein_ff == 'ff14sb':
                # changing co capitals SB so it will be accepted by tleap
                user_input_protein_ff = 'ff14SB'
                break
            elif user_input_protein_ff == 'ff15ipq':
                break
            elif user_input_protein_ff == 'fb15':
                break
            elif user_input_protein_ff == 'ff03':
                user_input_protein_ff = 'ff03.r1'
                break
            elif user_input_protein_ff == 'ff03ua':
                break
        except:
            print('Please, provide valid input')
    # saving choice to control file and tleap input
    save_to_file(f"ff = {user_input_protein_ff}\n", filename)
    with open(tleap_file, "a") as f:
        f.write(f"source leaprc.protein.{user_input_protein_ff}\n")
    # water force field
    water_ff_list = ['tip3p', 'tip4pew', 'spce']
    # getting box info based on the chosen water ff
    water_box_dict = {
        'tip3p': 'TIP3PBOX',
        'tip4pew': 'TIP4PEWBOX',
        'spce': 'SPCBOX',
    }
    # getting ions parameters based on the chosen water ff
    ions_dict = {
        'tip3p': 'frcmod.ionsjc_tip3p',
        'tip4pew': 'frcmod.ionsjc_tip4pew',
        'spce': 'frcmod.ionsjc_spce'
    }
    USER_CHOICE_WATER_FF = (
        f"\nPlease, choose force field which will be used for water during your simulations.\n"
        f"Please, note that the most common choice is tip3p.\n"
        f"The following options are available:\n"
        f"- 'tip3p'\n"
        f"- 'tip4pew'\n"
        f"- 'spce'\n"
        f"Please, provide your choice:\n"
    )
    while True:
        try:
            # getting user input
            user_input_water_ff = str(input(USER_CHOICE_WATER_FF).lower())
            if user_input_water_ff in water_ff_list:
                break
        except:
            print('Provided input is not valid')
    # saving water force field choice to control file and tleap input
    save_to_file(f"wat_ff = {user_input_water_ff}\n", filename)
    # getting ions parameters
    ions = ions_dict.get(user_input_water_ff)
    # water and ion parameters put into tleap input
    with open(tleap_file, "a") as f:
        f.write(f"loadoff solvents.lib\n")
        f.write(f"loadoff atomic_ions.lib\n")
        f.write(f"loadamberparams frcmod.{user_input_water_ff}\n")
        f.write(f"loadamberparams {ions}\n")
    # finding if there are ligands in control file
    ligands = r'ligands\s*=\s*\[(.*)\]'
    ligands_match = re.search(ligands, control)
    if ligands_match:
        # if there are ligands, find which force field was used
        lig_ff = r'atoms_type\s*=\s*(.*)'
        lig_ff_match = re.search(lig_ff, control).group(1)
        # saving match to tleap input
        with open(tleap_file, "a") as f:
            f.write(f"source leaprc.{lig_ff_match}\n")
        # taking only ligands entries
        ligands_match = ligands_match.group(1)
        # removing quotes from string
        ligands_string = ligands_match.replace("'", "")
        # removing whitespaces and turning string into a list
        ligands_list = re.sub(r'\s', '', ligands_string).split(',')
        # putting mol2 and frcmod for each ligand into tleap input
        for ligand in ligands_list:
            with open(tleap_file, 'a') as f:
                f.write(f"{ligand} = loadmol2 {ligand}.mol2\n")
                f.write(f"loadamberparams {ligand}.frcmod\n")
    # reading complex file
    with open(tleap_file, 'a') as f:
        f.write(f"mol = loadpdb {complex}\n")
        # checking complex pdb for validity
        f.write(f"check mol\n")
    # provide filaneme for topology and coordinates
    USER_CHOICE_NAME = "\nPlease, provide name for the prefix for the topology and coordinates files.\n" \
                       "Ideally, it should be just a few letters-long.\n" \
                       "For instance, if you type 'my_complex' your topology will be named my_complex.prmtop" \
                       " and coordinates will be named my_complex.inpcrd.\n" \
                       "Please, provide your choice:\n"
    while True:
        try:
            user_input_name = str(input(USER_CHOICE_NAME).lower())
            break
        except:
            print("Please, provide valid input")
    # saving chosen name to control file
    save_to_file(f"top_name = {user_input_name}\n", filename)
    # saving unsolvated file
    with open(tleap_file, 'a') as f:
        f.write(f"savepdb mol {user_input_name}_no_water.pdb\n")
    # determining solvation box size
    USER_CHOICE_WATERBOX_SIZE = (
        f"\nPlease, provide the size of a periodic solvent box around the complex (in Angstroms).\n"
        f"Most commonly used values are between 8 - 14.\n"
        f"Please, provide your choice:\n"
    )
    while True:
        try:
            user_input_waterbox_size = float(input(USER_CHOICE_WATERBOX_SIZE))
            # solvatebox must be positive
            if user_input_waterbox_size > 0:
                # solvatebox should be between 8 and 14 - if it is not, user is informed that it may be troublesome
                if user_input_waterbox_size < 8:
                    print(f"\nYou've chosen that solvent will create box of {user_input_waterbox_size} Angstroms around"
                          f"complex. This is smaller than the recommended size. Such a box might not be enough"
                          f"to properly solvate your complex.\n Please, proceed with caution")
                    break
                elif user_input_waterbox_size > 14:
                    print(f"\nYou've chosen that solvent will create box of {user_input_waterbox_size} Angstroms around"
                          f"complex. This is larger than the recommended size. A vast amount of water molecules might"
                          f"introduce very high computational cost.\n Please, proceed with caution."
                          f"might Please, proceed with caution")
                    break
                else:
                    break
        except:
            print('Please, provide valid input')
    # save waterbox size to control file
    save_to_file(f"box_size = {user_input_waterbox_size}\n", filename)
    # get box info
    waterbox = water_box_dict.get(user_input_water_ff)
    # save everything about solvation to tleap input
    with open(tleap_file, 'a') as f:
        f.write(f"solvatebox mol {waterbox} {user_input_waterbox_size}\n")
        f.write(f"addions mol Na+ 0\n")
        f.write(f"addions mol Cl- 0\n")
        f.write(f"savepdb mol {user_input_name}_solvated.pdb\n")
        f.write(f"saveamberparm mol {user_input_name}.prmtop {user_input_name}.inpcrd\n")
        f.write(f"quit\n")
    # tleap input from a command line
    tleap_run = f"tleap -f {tleap_file}"
    # execute tleap input
    subprocess.run([f"{tleap_run}"], shell=True)


top_prep_functions = [
    file_naming,
    clearing_control,
    hydrogen_check,
    ligands_parameters,
    antechamber_parmchk_input,
    pdb_process,
    tleap_input]

methods_generator = (y for y in top_prep_functions)


def queue_methods():
    next(methods_generator, None)
    global stop_generator
    stop_generator = False
    for x in top_prep_functions:
        x()
        # if a condition is met, generator is stopped
        if stop_generator:
            # I do not know if this prompt is necessary
            print('\nProgram has not finished normally - it appears that something was wrong with your structure. \n'
                  'Apply changes and try again!\n')
            break
