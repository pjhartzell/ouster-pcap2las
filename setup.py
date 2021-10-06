from setuptools import setup

setup(
    name='pcap2las',
    version='0.1.0',
    author="Preston Hartzell",
    author_email="preston.hartzell@gmail.com",
    packages=['pcap2las'],
    entry_points={
        'console_scripts': ['pcap2las=pcap2las.pcap2las:main']
    }
)