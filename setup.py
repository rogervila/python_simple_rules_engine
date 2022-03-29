from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='python_simple_rules_engine',
    packages=['python_simple_rules_engine'],
    version='CURRENT_VERSION',
    license='MIT',
    description='Evaluate rules based on a subject',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Roger Vilà',
    author_email='rogervila@me.com',
    url='https://github.com/rogervila/python_simple_rules_engine',
    download_url='https://github.com/rogervila/python_simple_rules_engine/archive/CURRENT_VERSION.tar.gz',
    keywords=['python rules engine'],
    install_requires=[
        'py_dto >= 0.4.0'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
    ],
)
