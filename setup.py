from pathlib import Path
from setuptools import setup, find_packages
import squeezer

version = '0.1'


description = 'A collection of tools to auto-generate everything needed to run a ground system.'
url = 'https://github.com/WindhoverLabs/auto-yamcs'
requires = [
    'PyYAML==5.3.1',
    'six==1.15.0',
    'wheel==0.35.1',
    'python-dateutil>=2.8.0',
    'pytest==6.1.1',
    'sqlite_utils==2.21',
    'scipy>=1.4.1',
    'cerberus==1.3.2',
]
with open("README.md", "r", encoding="utf-8") as fh:
    readme = fh.read()

setup(
    name='auto-yamcs',
    version=version,
    description=description,
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Windhover Labs',
    author_email='lgomez@windhoverlabs.com',
    url=url,
    license='3BSD-3-Clause',
    python_requires='>=3.6.0',
    install_requires=requires,
    packages=find_packages(),
    include_package_data=True,
    entry_points={'console_scripts': ['auto-yamcs = squeezer:main']},
    classifiers=[
        "License :: 3BSD-3-Clause",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
)