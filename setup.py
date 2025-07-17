from setuptools import setup, find_packages

setup(
    name='ccai',  # 🟢 CLI command will be `ccai`
    version='0.1.0',
    description='A CLI and Python client for sending SMS via CloudContactAI',
    author='CloudContactAI LLC',
    license='MIT',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests>=2.31.0',
        'pydantic>=2.5.0'
    ],
    entry_points={
        'console_scripts': [
            'ccai = ccai_python.ccai:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
