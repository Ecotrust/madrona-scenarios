import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='madrona-scenarios',
    version='0.0.1',
    packages=['scenarios'],
    install_requires=[
        'django-flatblocks',
        'django-picklefield',
        'xmltodict',
    ],
    include_package_data=True,
    license='TBD',
    description='Scenarios for Madrona',
    long_description=README,
    url='http://www.pointnineseven.com/path/to/opensource/info',
    author='Point97, LLC',
    author_email='nobody@pointnineseven.com',
    classifiers=[
        'Environment :: Web Development',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: TBD',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
