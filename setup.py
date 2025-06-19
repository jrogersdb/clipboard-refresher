from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="clipboard-refresher",
    version="0.1.0",
    author="Jonathan Rogers",
    author_email="jrogers@databank.com",
    description="A Windows system tray application that monitors clipboard activity from RDP sessions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jrogersdb/clipboard-refresher",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.7',
    install_requires=[
        'pystray>=0.19.5',
        'pywin32>=306',
        'Pillow>=10.0.0',
    ],
    entry_points={
        'console_scripts': [
            'clipboard-refresher=clipboard_refresher.main:main',
        ],
    },
)
