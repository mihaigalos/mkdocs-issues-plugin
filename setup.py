from setuptools import setup, find_packages


setup(
    name='mkdocs-breadcrumbs',
    version='0.0.1',
    description='Location-based breadcrumbs.',
    long_description='Location-based breadcrumbs.',
    keywords='mkdocs',
    url='https://github.com/mihaigalos/mkdocs-breadcrumbs',
    author='Mihai Galos',
    author_email='mihai@galos.one',
    license='MIT',
    python_requires='>=3',
    install_requires=[
        'mkdocs>=1.0.4',
        'mkdocs-material'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'breadcrumbs = mkdocs_breadcrumbs.plugin:BreadCrumbs'
        ]
    }
)
