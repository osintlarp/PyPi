from setuptools import setup, find_packages

setup(
    name="socmint",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4"
    ],
    author="imposd",
    description="SOCMINT scraping toolkit",
    url="https://github.com/yourrepo/socmint"
)
