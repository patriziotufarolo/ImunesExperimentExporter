from setuptools import setup, find_packages
import os

setup(
    name='ImunesExperimentExporter',
    version='1.0',
    packages=find_packages(),
    url='https://blog.tufarolo.eu',
    license='GPLv3',
    author='Patrizio Tufarolo',
    author_email='patriziotufarolo@gmail.com',
    description='Snippet to export and import changes made to an IMUNES experiment at runtime, on Linux.  It calculates deltas between the base Docker image and the actual container situation, then saves differences on the filesystem. The script can also load changes back.  I\'ve written it to facilitate students to save their work at my networking lab class.',
    entry_points={
        'console_scripts': [
            "imunes-export = ImunesExperimentExporter.__main__:main"
        ]
    },
    include_package_data = True,
    package_data = {
        '': ['*.txt'],
        '': ['LICENSE'],
        '': ['README'],
        '': ['*.glade']
    }
)