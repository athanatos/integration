from setuptools import setup, find_packages

setup(
    name='IntegrationBranchManager',
    version='0.0.0',
    packages=find_packages(),
    author='Samuel Just',
    description='Integration branch manager',
    liscense='MIT',
    keywords='testing git',
    entry_points={
        'console_scripts': [
            'ic-manager = ic_manager:main'
        ],
    },
)
