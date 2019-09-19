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
    extras_require={
        "dev": [
            "asynctest==0.13.0",
            "async-asgi-testclient==1.0.3",
            "pytest==5.1.2",
            "pytest-asyncio==0.10.0",
            "pytest-randomly==3.1.0",
            "requests==2.22.0",
        ]
    },
)
