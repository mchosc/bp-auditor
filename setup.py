from setuptools import setup, find_packages

setup(
    name='bp-auditor',
    version='0.1a0',
    author='Guillermo Rodriguez',
    author_email='guillermo@telos.net',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'bpaudit = bp_auditor.cli:bpaudit'
        ]
    },
    install_requires=[
        'trio==0.22.2',
        'asks',
        'click',
        'openpyxl',
        'telebot',
        'anyio~=3.0'
    ],
)
