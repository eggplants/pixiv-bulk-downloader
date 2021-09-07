from typing import List

from setuptools import find_packages, setup  # type: ignore

"""Update:
(change version,)
sudo rm -rf build dist *.egg-info
python setup.py sdist bdist_wheel
python -m twine upload --repository pypi dist/*
"""


def parse_requires():
    # type: () -> List[str]
    d = open('requirements.txt').read()
    return d.replace('\r', '').rstrip().split('\n')


setup(
    name='pixiv-bulk-downloader',
    version='2.0',
    description='Pixiv Bulk Downloader',
    description_content_type='',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/eggplants/pixiv-bulk-downloader',
    author='eggplants',
    packages=find_packages(),
    python_requires='>=3.5',
    include_package_data=True,
    license='MIT',
    install_requires=parse_requires(),
    entry_points={
        'console_scripts': [
            'pbd=pbd.main:main'
        ]
    }
)
