genetic_circuit_scoring
########################################

gls_score_circuit is a Python app for scoring circuit mappings produced from genetic logic synthesis. It includes a class called CircuitMapping that defines methods for the following:

1. Loading a circuit mapping.

2. Scoring a circuit mapping.

3. Tuning the gate parameters for a circuit mapping.

.. contents::

.. section-numbering::

Specification
=============

The arguments to gls_score_circuit Python app are listed below.

.. code-block:: powershell

	-l, --library     [path to genetic gate library JSON file]
	-m, --mapping     [path to genetic circuit mapping JSON file]
	-t, --tuning      [optional path to genetic circuit tuning]

Examples
========

An example of running the gls_score_circuit Python app from the Command Prompt after installing it and changing your working directory to genetic_circuit_scoring is shown below.

.. code-block:: powershell

    gls_score_circuit -l 'examples\genetic_gate_library.json' -m 'examples\majority_mapping.json'

Equivalently, you can import the CircuitMapping class and use it as shown:

.. code-block:: python

    import json
    from genetic_circuit_scoring import CircuitMapping

    with open('examples\genetic_gate_library.json') as library_file:
        library_data = json.load(library_file)
    with open('examples\majority_mapping.json') as majority_mapping_file:
        majority_mapping_data = json.load(majority_mapping_file)

    circuit_mapping = CircuitMapping(library_data)
    circuit_mapping.map(majority_mapping_data)

    circuit_mapping.score()

If you wish to tune a circuit mapping before scoring, simply include the -t argument to the gls_score_circuit Python app like so:

.. code-block:: powershell

    gls_score_circuit -l 'examples\genetic_gate_library.json' -m 'examples\majority_mapping.json' -t 'examples\majority_tuning.json'

Equivalently, you can call the tune method of the CircuitMapping class:

.. code-block:: python

    import json
    from genetic_circuit_scoring import CircuitMapping

    with open('examples\genetic_gate_library.json') as library_file:
        library_data = json.load(library_file)
    with open('examples\majority_mapping.json') as majority_mapping_file:
        majority_mapping_data = json.load(majority_mapping_file)
    with open('examples\majority_tuning.json') as majority_tuningfile:
        majority_tuning_data = json.load(majority_tuningfile)

    circuit_mapping = CircuitMapping(library_data)
    circuit_mapping.map(majority_mapping_data)

    circuit_mapping.tune(majority_tuning_data)

    circuit_mapping.score()