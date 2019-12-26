import re
from setuptools import setup, find_packages

VERSIONFILE = "apachescan/__version__.py"
REQUIREMENTS = []


def get_version():
    verstrline = open(VERSIONFILE, "rt").read()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    version_parsed = re.search(VSRE, verstrline, re.M)
    if version_parsed:
        version = version_parsed.group(1)
    else:
        raise RuntimeError(
            "Unable to find version string in %s." % (VERSIONFILE,))
    return version


with open("requirements.txt", 'r') as f:
    REQUIREMENTS = f.readlines()

setup(
    name='apachescan',
    version=get_version(),
    description='Module scanning Apache HTTP Server log',
    license="BSD",
    provides=["apachescan"],
    author='Quintin Jean-Noel',
    author_email='quintin.jeannoel@gmail.com',
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts': [
            'apachescand = apachescan.daemon:main']
    },
    test_suite='nose.collector',
)
