import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='ssplib',
    version='0.0.1',
    author='Nico Strasdat',
    author_email='nstrasdat@gmail.com',
    description='Arcflow formulations for the SSP',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/wotzlaff/ssp-arcflow',
    packages=setuptools.find_packages(),
    classifiers=[],
    python_requires='>=3.6',
)