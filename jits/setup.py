import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'Chameleon==2.22',
    'Jinja2==2.8',
    'Mako==1.0.1',
    'MarkupSafe==0.23',
    'PasteDeploy==1.5.2',
    'Pygments==2.0.2',
    'SQLAlchemy==1.0.8',
    'WebOb==1.4.1',
    'argparse==1.2.1',
    'pyramid==1.5.7',
    'pyramid-chameleon==0.3',
    'pyramid-debugtoolbar==2.4',
    'pyramid-jinja2==2.5',
    'pyramid-mako==1.0.2',
    'pyramid-tm==0.12',
    'repoze.lru==0.6',
    'transaction==1.4.4',
    'translationstring==1.3',
    'venusian==1.0',
    'waitress==0.8.9',
    'wsgiref==0.1.2',
    'zope.deprecation==4.1.2',
    'zope.interface==4.1.2',
    'zope.sqlalchemy==0.7.6',
    ]

setup(name='jits',
      version='0.0',
      description='jits',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='jits',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = jits:main
      [console_scripts]
      initialize_jits_db = jits.scripts.initializedb:main
      """,
      )
