from setuptools import setup, find_packages

setup(
    name="league_admin",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyyaml>=6.0.2',
        'pandas>=2.2.3',
        'ortools',  # for constraint programming
    ],
) 