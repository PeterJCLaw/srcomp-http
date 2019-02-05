from setuptools import setup, find_packages


with open('README.rst') as f:
    long_description = f.read()

setup(
    name='sr.comp.http',
    version='1.1.1',
    packages=find_packages(),
    namespace_packages=['sr', 'sr.comp'],
    package_data={'sr.comp.http': ['logging-*.ini']},
    long_description=long_description,
    author="Student Robotics Competition Software SIG",
    author_email="srobo-devel@googlegroups.com",
    install_requires=[
        'PyYAML >=3.11, <5',
        'sr.comp >=1.1, <2',
        'six >=1.8, <2',
        'Flask >=1.0, <2',
        'simplejson >=3.6, <4',
        'python-dateutil >=2.2, <3',
    ],
    setup_requires=[
        'Sphinx >=1.3, <2',
    ],
    entry_points={
        'console_scripts': [
            'srcomp-update = sr.comp.http.update:main'
        ]
    },
    tests_require=[
        'nose >=1.3, <2',
        'freezegun >=0.2.8, <0.4',
        'mock >=1.0.1, <2',
    ],
    test_suite='nose.collector'
)
