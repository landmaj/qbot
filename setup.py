from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="qbot",
    version="0.0.1",
    packages=find_packages(exclude=["tests"]),
    url="https://github.com/landmaj/qbot",
    author="Michał Wieluński",
    author_email="michal@w-ski.dev",
    install_requires=requirements,
)
