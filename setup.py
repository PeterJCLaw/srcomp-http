from setuptools import find_namespace_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='sr.comp.http',
    version='1.6.0',
    url='https://github.com/PeterJCLaw/srcomp-http',
    project_urls={
        'Documentation': 'https://srcomp-http.readthedocs.org/',
        'Code': 'https://github.com/PeterJCLaw/srcomp-http',
        'Issue tracker': 'https://github.com/PeterJCLaw/srcomp-http/issues',
    },
    packages=find_namespace_packages(exclude=('tests',)),
    namespace_packages=['sr', 'sr.comp'],
    package_data={'sr.comp.http': ['logging-*.ini']},
    description="HTTP API for Student Robotics Competition Software",
    long_description=long_description,
    author="Student Robotics Competition Software SIG",
    author_email="srobo-devel@googlegroups.com",
    install_requires=[
        'sr.comp >=1.2, <2',
        # `Flask.json_encoder` is removed in 2.3. Unfortunately its replacement
        # was only added in 2.2 (!), so supporting wider versions is tricky.
        # Limit what we support for now.
        'Flask >=1, <2.3',
        'Werkzeug >= 2, <3',
        'simplejson >=3.6, <4',
        'python-dateutil >=2.2, <3',
        'typing-extensions >=3.7.4.2, <5',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'srcomp-update = sr.comp.http.update:main',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    zip_safe=False,
)
