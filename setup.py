"""Setup config for System."""
from setuptools import setup

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='system',
    url='https://github.com/ChipMcCallahan/System',
    author='Chip McCallahan',
    author_email='thisischipmccallahan@gmail.com',
    # Needed to actually package something
    packages=['system'],
    package_dir={'system': 'src'},
    # Needed for dependencies
    install_requires=[
        'versatuple @ git+https://github.com/ChipMcCallahan/Versatuple',
        'pypika',
        'sqlite3'
    ],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='LICENSE',
    description='Utils intended for author\'s personal use.',
    # We will also need a readme eventually (there will be a warning)
    # long_description=open('README.txt').read(),
)