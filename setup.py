from setuptools import find_packages, setup

"""Update:
(change version,)
sudo rm -rf build dist *.egg-info
python setup.py sdist bdist_wheel
python -m twine upload --repository pypi dist/*
"""

setup(
    name='pixiv-bulk-downloader',
    version='0.0.7',
    description='Pixiv Bulk Downloader',
    description_content_type='',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/eggplants/pixiv-bulk-downloader',
    author='eggplants',
    packages=find_packages(),
    python_requires='>=3.0',
    include_package_data=True,
    license='MIT',
    install_requires=['PixivPy'],
    entry_points={
        'console_scripts': [
            'pbd=main:main'
        ]
    }
)
