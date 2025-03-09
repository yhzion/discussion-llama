from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="discussion-llama",
    version="0.1.0",
    author="Discussion-Llama Team",
    author_email="example@example.com",
    description="A multi-role discussion system using language models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/discussion-llama",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "discussion-llama=discussion_llama.cli.cli:main",
        ],
    },
) 