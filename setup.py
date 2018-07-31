from setuptools import setup

setup(name='genetic_logic_synthesis',
      version='0.1',
      description='Tools for genetic logic synthesis (GLS)',
      url='https://github.com/BDAthlon/genetic_logic_synthesis',
      author='Nicholas Roehner',
      author_email='nicholasroehner@gmail.com',
      packages=['genetic_circuit_scoring'],
      entry_points={
          'console_scripts': [
              'gls_score_circuit = genetic_circuit_scoring.score_circuit:main'
          ]
      },
      zip_safe=False)