from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dot-spend",
    version="2.0.0",
    author="Yehia Gewily",
    author_email="yehia@example.com",
    description="A powerful CLI expense tracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YehiaGewily/dot-spend",
    packages=find_packages(),
    py_modules=["main", "config", "utils", "data", "datastore", "history", 
                "exporters", "insights", "migrations", "categorization", 
                "deduplication", "recurring", "currency"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "spend=main:app",
        ],
    },
)
