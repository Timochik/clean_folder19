from setuptools import setup, find_namespace_packages

setup(
    name='clean_folder19',
    version='0.0.2',
    description='Very useful code',
    author='Svirhun Tymofii',
    author_email='ttimofej983@gmail.com',
    license='MIT',
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_namespace_packages(),
    entry_points={'console_scripts': ['main=clean_folder19.clean:main']}
)
