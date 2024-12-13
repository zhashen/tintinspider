from setuptools import setup, find_packages

setup(
    name='tintinspider',
    version='0.1',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'ttspider = tintinspider.cli:main'
        ]
    },
)