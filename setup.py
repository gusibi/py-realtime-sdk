#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="py-realtime-sdk",
      version="0.1.0",
      description="LeanCloud Realtime Message Python SDK",
      license="BSD",
      install_requires=["ujson", "requests", "six", "chardet"],
      author="gusibi",
      author_email="cacique1103@gmail.com",
      url="https://github.com/gusibi/py-realtime-sdk",
      download_url="https://github.com/gusibi/py-realtime-sdk/archive/master.zip",
      packages=find_packages(),
      keywords=["python-leancloud", "leancloud", "realtime", "sdk"],
      zip_safe=True)
