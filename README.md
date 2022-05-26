[![DOI](https://zenodo.org/badge/366323997.svg)](https://zenodo.org/badge/latestdoi/366323997)

# HOGBEN
**H**olistic **O**ptimization for **G**enerating **B**etter **E**xperimental **N**eutrons


`pip install HOGBEN`

## About the Project
**For the original repository that this work is based on, see [fisher-information](https://github.com/James-Durant/fisher-information)**.

Using the Fisher information (FI), the design of neutron reflectometry experiments can be optimised, leading to greater confidence in parameters of interest and better use of experimental time. This repository contains the [code](/experimental-design), [data](/experimental-design/data) and [results](/experimental-design/results) for optimising the design of a wide range of reflectometry experiments.

Please refer to the [notebooks](/notebooks) directory for an introduction.


This repository is named after Lancelot Hogben, whose relentless opposition of eugenics (and vocal criticism of Ronald Fisher's views on it) we applaud.

### Citation
Please cite the following [article](https://arxiv.org/abs/2108.05605) if you intend on including elements of this work in your own publications:
> Durant, J. H., Wilkins, L. and Cooper, J. F. K. Optimising experimental design in neutron reflectometry. arXiv:2108.05605 (2021).

Or with BibTeX as:
```
@misc{Durant2021,
   title         = {Optimising experimental design in neutron reflectometry}, 
   author        = {Durant, J. H. and Wilkins, L. and Cooper, J. F. K.},
   year          = {2021},
   eprint        = {2108.05605},
   archivePrefix = {arXiv},
   primaryClass  = {physics.data-an}
}
```

For the results presented in this article, see [notebooks](/notebooks), and for the figures, see [figures](/figures).

## Installation
1. To replicate the development environment with the [Anaconda](https://www.anaconda.com/products/individual) distribution, first create an empty conda environment by running: <br /> ```conda create --name experimental-design python=3.8.3```

2. To activate the environment, run: ```conda activate experimental-design```

3. Install pip by running: ```conda install pip```

4. Run the following to install the required packages from the [requirements.txt](/requirements.txt) file: <br />
   ```pip install -r requirements.txt```

You should now be able to run the code. Please ensure you are running a version of Python >= 3.8.0 \
If you are running an old version of Anaconda, you may need to reinstall with a newer version for this.

## Contact
Jos Cooper - jos.cooper@stfc.ac.uk \
James Durant - james.durant@warwick.ac.uk \
Lucas Wilkins - lucas@lucaswilkins.com

## Acknowledgements
We thank Luke Clifton for his assistance and expertise in fitting the lipid monolayer and lipid bilayer data sets.

## License
Distributed under the GPL-3.0 License. See [license](/LICENSE) for more information.
