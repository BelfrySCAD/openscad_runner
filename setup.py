#!/usr/bin/env python

from setuptools import setup

VERSION = "1.0.9"


with open('README.rst') as f:
    LONG_DESCR = f.read()

data_files = []

setup(
    name='openscad_runner',
    version=VERSION,
    description='A Python library to interface with the OpenSCAD app.',
    long_description=LONG_DESCR,
    long_description_content_type='text/x-rst',
    author='Revar Desmera',
    author_email='revarbat@gmail.com',
    url='https://github.com/revarbat/openscad_runner',
    download_url='https://github.com/revarbat/openscad_runner/archive/v1.0.8.zip',
    packages=['openscad_runner'],
    license='MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
        'Topic :: Multimedia :: Graphics :: 3D Rendering',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='openscad interface',
    install_requires=[
        'setuptools',
        'Pillow>=7.2.0',
        'pygifsicle>=1.0.2'
    ],
    data_files=data_files,
)

