from setuptools import setup, find_packages
from glob import glob
import os.path

with open("README.md", "r") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'txtrader_monitor', 'version.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name="txtrader-monitor",
    version=about['VERSION'],
    author="Matt Krueger",
    author_email="mkrueger@rstms.net",
    description="TxTrader Securities Trading API Monitor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url='https://github.com/rstms/txtrader_monitor/',
    keywords='trading api txtrader twisted',
    packages=find_packages(exclude=('tests', 'docs')),
    data_files=[('.', ['LICENSE', 'requirements.txt'])],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires='>=3.7',
    install_requires=['twisted>=20.3.0', 'click>=7.1.2', 'ujson>=3.0.0'],
    tests_require=['pytest', 'tox', 'yapf', 'twine', 'wheel', 'pybump'],
    entry_points={
        'console_scripts': [
            'txtrader_monitor=txtrader_monitor:txtrader_monitor',
        ],
    },
)
