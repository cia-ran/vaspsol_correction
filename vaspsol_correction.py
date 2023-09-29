#!/usr/bin/env python3

import os
import sys
from ase import Atoms
from ase.io import read



def get_job_name():
	'''
	Function that determines the job name of the most recent calculation in the directory.
	'''
	dir_list = os.listdir()
	job_list = [i.rstrip().split('.') for i in dir_list if '.out' in i]
	max_jobid = (str(max(i[1] for i in job_list)))
	job_index = [i[1] for i in job_list].index(max_jobid)
	return job_list[job_index][0] + '.{}'.format(max_jobid) + '.out'

def get_raw_energy():
	'''
	Function that pulls the raw DFT output energy from the VASPsol output files.
	'''
	with open('OSZICAR', 'r') as oszicar:
		lines = list(oszicar)
		check = ['F=', 'E0=', 'd', 'E']
		energy_list = []
		for i in lines:
			line = i.rstrip().split()
			if all([item in line for item in check]) == True:
				energy_list.append(float(line[4]))
			else:
				continue
	return energy_list[-1]


def get_ne_final_fermi():
	'''
	Function that pulls the final number of electrons (after relaxation) and fermi shift from the MyVASPJob.x.out file.
	'''
	job_name = get_job_name()
	if 'single' in job_name:
		with open('{}'.format(job_name), 'r') as outfile:
			lines = list(outfile)
			line = lines[1]
			line = line.rstrip().split()
			ne_final = float(line[0])
			fermi_shift = float(line[1])
	elif 'My' in job_name:
		with open('{}'.format(job_name), 'r') as outfile:
			lines = list(outfile)
			line = lines[-1]
			line = line.rstrip().split()
			ne_final = float(line[1])
			fermi_shift = float(line[2])
	else:
		print('Don\'t recognise .out file.\n')

	return ne_final, fermi_shift


def get_ne_initial():
	'''
	Function that calculates the initial number of electrons (before relaxation) from the CONTCAR and POTCAR.
	'''
	element_dict = {'element': [], 'zval': [], 'Natoms': []}

	with open('POTCAR', 'r') as potcar:
		for line in potcar:
			if 'TITEL' in line:
				line = line.rstrip().split()
				element = line[3]
				if len(element) > 2:
					element = element[:2]
				element_dict['element'].append(element)
			if 'POMASS' in line:
				line = line.rstrip().split()
				element_dict['zval'].append(float(line[5]))

	contcar = read('CONTCAR')
	symbols = contcar.get_chemical_symbols()
	for i in element_dict['element']:
		element_dict['Natoms'].append(symbols.count(i))

	ne_initial = 0
	for i in list(range(len(element_dict['Natoms']))):
		ne_initial += element_dict['zval'][i] * element_dict['Natoms'][i]

	return ne_initial


def get_mu_e():
	'''
	Function that pulls mu(e) from the submit.sl file.
	'''
	slurm_file = [i for i in os.listdir() if '.sl' in i]
	with open ('{}'.format(slurm_file[0])) as submit_file:
		for line in submit_file:
			if 'utarget=' in line:
				line = line.rstrip().split('=')
				utarget = float(line[1])
			elif 'phiref=' in line:
				line = line.rstrip().split('=')
				phiref = float(line[1])
	return -phiref - utarget


		
raw_energy = get_raw_energy()
ne_final, fermi_shift = get_ne_final_fermi()
ne_initial = get_ne_initial()
mu_e = get_mu_e()
net_charge = ne_initial - ne_final

fermi_correction = net_charge * (-1*fermi_shift)
fermi_corrected_energy = raw_energy + fermi_correction

electron_correction = net_charge * mu_e
final_corrected_energy = fermi_corrected_energy + electron_correction

print('''
The raw energy is {},
the net charge is {},
the Fermi shift is {},
\u03BC\u2091 is {},
the Fermi corrected energy is {},
the Fermi and electron (full) corrected energy is {}'''.format(raw_energy, net_charge, fermi_shift, mu_e, fermi_corrected_energy, final_corrected_energy))

