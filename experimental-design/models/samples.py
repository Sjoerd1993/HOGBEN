import matplotlib.pyplot as plt
import numpy as np
import os, sys
sys.path.append(os.path.join(__file__, '..'))
plt.rcParams['figure.figsize'] = (9,7)
plt.rcParams['figure.dpi'] = 600

import refnx.dataset, refnx.reflect, refnx.analysis
import refl1d.material, refl1d.model, refl1d.probe, refl1d.experiment, refl1d.magnetism
import bumps.parameter, bumps.fitproblem

from base import BaseSample
from simulate import simulate, refl1d_experiment, reflectivity
from utils import fisher, Sampler, save_plot

class Sample(BaseSample):
    """Wrapper class for a standard refnx or Refl1D reflectometry sample.

    Attributes:
        structure (refnx.reflect.Structure or refl1d.model.Stack): refnx or Refl1D sample.
        name (str): name of the sample.
        params (list): varying parameters of sample.

    """
    def __init__(self, structure):
        self.structure = structure
        self.name = structure.name
        self.params = Sample.__vary_structure(structure)

    @staticmethod
    def __vary_structure(structure, bound_size=0.2):
        """Varies the SLD and thickness of each layer of a given `structure`.

        Args:
            structure (refnx.reflect.Structure or refl1d.model.Stack): structure to vary.
            bound_size (float): size of bounds to place on varying parameters.

        Returns:
            list: varying parameters of sample.

        """
        params = []
        # The structure was defined in refnx.
        if isinstance(structure, refnx.reflect.Structure):
            # Vary the SLD and thickness of each component (layer).
            for component in structure[1:-1]:
                sld = component.sld.real
                sld_bounds = (sld.value*(1-bound_size), sld.value*(1+bound_size))
                sld.setp(vary=True, bounds=sld_bounds)
                params.append(sld)

                thick = component.thick
                thick_bounds = (thick.value*(1-bound_size), thick.value*(1+bound_size))
                thick.setp(vary=True, bounds=thick_bounds)
                params.append(thick)

        # The structure was defined in Refl1D.
        elif isinstance(structure, refl1d.model.Stack):
            # Vary the SLD and thickness of each component (layer).
            for component in structure[1:-1]:
                sld = component.material.rho
                sld.pmp(bound_size*100)
                params.append(sld)

                thick = component.thickness
                thick.pmp(bound_size*100)
                params.append(thick)

        # Otherwise the structure is invalid.
        else:
            raise RuntimeError('invalid structure given')

        return params

    def angle_info(self, angle_times, contrasts=None):
        """Calculates the Fisher information matrix for a sample measured over a number of angles.

        Args:
            angle_times (list): points and counting times for each measurement angle to simulate.

        Returns:
            numpy.ndarray: Fisher information matrix.

        """
        model, data = simulate(self.structure, angle_times)
        qs, counts, models = [data[:,0]], [data[:,3]], [model]
        return fisher(qs, self.params, counts, models)

    def sld_profile(self, save_path):
        """Plots the SLD profile of the sample.

        Args:
            save_path (str): path to directory to save SLD profile to.

        """
        # Currently not defined for Refl1D samples.
        if isinstance(self.structure, refnx.reflect.Structure):
            z, slds = self.structure.sld_profile()
            
        elif isinstance(self.structure, refl1d.model.Stack):
            q = np.geomspace(0.005, 0.3, 500)
            scale, bkg, dq = 1, 1e-6, 2
            experiment = refl1d_experiment(self.structure, q, scale, bkg, dq)
            z, slds, _ = experiment.smooth_profile()
            
        else:
            raise RuntimeError('invalid structure given')

        fig = plt.figure()
        ax = fig.add_subplot(111)

        # Plot the SLD profile.
        ax.plot(z, slds, color='black', label=self.name)

        ax.set_xlabel('$\mathregular{Distance\ (\AA)}$', fontsize=11, weight='bold')
        ax.set_ylabel('$\mathregular{SLD\ (10^{-6} \AA^{-2})}$', fontsize=11, weight='bold')

        # Save the plot.
        save_path = os.path.join(save_path, self.name)
        save_plot(fig, save_path, 'sld_profile')

    def reflectivity_profile(self, save_path, q_min=0.005, q_max=0.4, points=500, scale=1, bkg=1e-7, dq=2):
        """Plots the reflectivity profile of the sample.

        Args:
            save_path (str): path to directory to save reflectivity profile to.
            q_min (float): minimum Q value to plot.
            q_max (float): maximum Q value to plot.
            points (int): number of points to plot.
            scale (float): experimental scale factor.
            bkg (float): level of instrument background noise.
            dq (float): instrument resolution.

        """
        q = np.geomspace(q_min, q_max, points)
        if isinstance(self.structure, refnx.reflect.Structure):
            model = refnx.reflect.ReflectModel(self.structure, scale=scale, bkg=bkg, dq=dq)
            
        elif isinstance(self.structure, refl1d.model.Stack):
            model = refl1d_experiment(self.structure, q, scale, bkg, dq)
            
        else:
            raise RuntimeError('invalid structure given')

        r = reflectivity(q, model) # Calculate the model reflectivity.

        # Plot the model reflectivity against Q.
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(q, r, color='black')

        ax.set_xlabel('$\mathregular{Q\ (Å^{-1})}$', fontsize=11, weight='bold')
        ax.set_ylabel('Reflectivity (arb.)', fontsize=11, weight='bold')
        ax.set_yscale('log')

        # Save the plot.
        save_path = os.path.join(save_path, self.name)
        save_plot(fig, save_path, 'reflectivity_profile')

    def nested_sampling(self, angle_times, save_path, filename, dynamic=False):
        """Runs nested sampling on simulated data of the sample.

        Args:
            angle_times (list): points and counting times for each measurement angle to simulate.
            save_path (str): path to directory to save corner plot to.
            filename (str): name of file to save corner plot to.
            dynamic (bool): whether to use static or dynamic nested sampling.

        """
        model, data = simulate(self.structure, angle_times)

        if isinstance(self.structure, refnx.reflect.Structure):
            dataset = refnx.reflect.ReflectDataset([data[:,0], data[:,1], data[:,2]])
            objective = refnx.anaylsis.Objective(model, dataset)

        elif isinstance(self.structure, refl1d.model.Stack):
            objective = bumps.fitproblem.FitProblem(model)
            
        else:
            raise RuntimeError('invalid structure given')
            
        # Sample the objective using nested sampling.
        sampler = Sampler(objective)
        fig = sampler.sample(dynamic=dynamic)

        # Save the sampling corner plot.
        save_path = os.path.join(save_path, self.name)
        save_plot(fig, save_path, filename+'_nested_sampling')

    def to_refl1d(self):
        """Converts a standard refnx structure to an equivalent Refl1D structure.
    
        Args:
            sample (refnx.reflect.Structure): refnx structure to convert.
    
        Returns:
            refl1d.model.Stack: equivalent structure defined in Refl1D.
    
        """
        # Iterate over each component.
        structure = refl1d.material.SLD(rho=0, name='Air')
        for component in self.structure[1:]:
            name, sld = component.name, component.sld.real.value,
            thick, rough = component.thick.value, component.rough.value
    
            # Add the component in the opposite direction to the refnx definition.
            structure = refl1d.material.SLD(rho=sld, name=name)(thick, rough) | structure
    
        structure.name = self.structure.name
        self.structure = structure
    
    def to_refnx(self):
        # Iterate over each component.
        structure = refnx.reflect.SLD(0, name='Air')
        for component in list(reversed(self.structure))[1:]:
            name, sld = component.name, component.material.rho.value,
            thick, rough = component.thickness.value, component.interface.value
            
            structure |= refnx.reflect.SLD(sld, name=name)(thick, rough)
    
        structure.name = self.structure.name
        self.structure = structure

def simple_sample():
    """Defines a simple sample.

    Returns:
        structures.Sample: structure in format for information calculation.

    """
    air = refnx.reflect.SLD(0, name='Air')
    layer1 = refnx.reflect.SLD(4, name='Layer 1')(thick=100, rough=2)
    layer2 = refnx.reflect.SLD(8, name='Layer 2')(thick=150, rough=2)
    substrate = refnx.reflect.SLD(2.047, name='Substrate')(thick=0, rough=2)

    structure = air | layer1 | layer2 | substrate
    structure.name = 'simple_sample'
    return Sample(structure)

def many_param_sample():
    """Defines a sample with many parameters.

    Returns:
        structures.Sample: structure in format for information calculation.

    """
    air = refnx.reflect.SLD(0, name='Air')
    layer1 = refnx.reflect.SLD(2.0, name='Layer 1')(thick=50, rough=6)
    layer2 = refnx.reflect.SLD(1.7, name='Layer 2')(thick=15, rough=2)
    layer3 = refnx.reflect.SLD(0.8, name='Layer 3')(thick=60, rough=2)
    layer4 = refnx.reflect.SLD(3.2, name='Layer 4')(thick=40, rough=2)
    layer5 = refnx.reflect.SLD(4.0, name='Layer 5')(thick=18, rough=2)
    substrate = refnx.reflect.SLD(2.047, name='Substrate')(thick=0, rough=2)

    structure = air | layer1 | layer2 | layer3 | layer4 | layer5 | substrate
    structure.name = 'many_param_sample'
    return Sample(structure)

def thin_layer_sample_1():
    """Defines a 2-layer sample with thin layers.

    Returns:
        structures.Sample: structure in format for information calculation.

    """
    air = refnx.reflect.SLD(0, name='Air')
    layer1 = refnx.reflect.SLD(4, name='Layer 1')(thick=200, rough=2)
    layer2 = refnx.reflect.SLD(6, name='Layer 2')(thick=6, rough=2)
    substrate = refnx.reflect.SLD(2.047, name='Substrate')(thick=0, rough=2)

    structure = air | layer1 | layer2 | substrate
    structure.name = 'thin_layer_sample_1'
    return Sample(structure)

def thin_layer_sample_2():
    """Defines a 3-layer sample with thin layers.

    Returns:
        structures.Sample: structure in format for information calculation.

    """
    air = refnx.reflect.SLD(0, name='Air')
    layer1 = refnx.reflect.SLD(4, name='Layer 1')(thick=200, rough=2)
    layer2 = refnx.reflect.SLD(5, name='Layer 2')(thick=30, rough=6)
    layer3 = refnx.reflect.SLD(6, name='Layer 3')(thick=6, rough=2)
    substrate = refnx.reflect.SLD(2.047, name='Substrate')(thick=0, rough=2)

    structure = air | layer1 | layer2 | layer3 | substrate
    structure.name = 'thin_layer_sample_2'
    return Sample(structure)

def similar_sld_sample_1():
    """Defines a 2-layer sample with layers of similar SLD.

    Returns:
        structures.Sample: structure in format for information calculation.

    """
    air = refnx.reflect.SLD(0, name='Air')
    layer1 = refnx.reflect.SLD(0.9, name='Layer 1')(thick=80, rough=2)
    layer2 = refnx.reflect.SLD(1.0, name='Layer 2')(thick=50, rough=6)
    substrate = refnx.reflect.SLD(2.047, name='Substrate')(thick=0, rough=2)

    structure = air | layer1 | layer2 | substrate
    structure.name = 'similar_sld_sample_1'
    return Sample(structure)

def similar_sld_sample_2():
    """Defines a 3-layer sample with layers of similar SLD.

    Returns:
        structures.Sample: structure in format for information calculation.

    """
    air = refnx.reflect.SLD(0, name='Air')
    layer1 = refnx.reflect.SLD(3.0, name='Layer 1')(thick=50, rough=2)
    layer2 = refnx.reflect.SLD(5.5, name='Layer 2')(thick=30, rough=6)
    layer3 = refnx.reflect.SLD(6.0, name='Layer 3')(thick=35, rough=2)
    substrate = refnx.reflect.SLD(2.047, name='Substrate')(thick=0, rough=2)

    structure = air | layer1 | layer2 | layer3 | substrate
    structure.name = 'similar_sld_sample_2'
    return Sample(structure)

if __name__ == '__main__':
    structures = [simple_sample, many_param_sample,
                  thin_layer_sample_1, thin_layer_sample_2,
                  similar_sld_sample_1, similar_sld_sample_2]

    save_path = '../results'

    # Plot the SLD and reflectivity profiles of all structures in this file.
    for structure in structures:
        sample = structure()
        
        sample.sld_profile(save_path)    
        sample.reflectivity_profile(save_path)
        
        plt.close('all')
        