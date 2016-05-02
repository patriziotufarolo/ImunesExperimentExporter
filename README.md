# Imunes Experiment Exporter

*Patrizio Tufarolo*

Snippet providing functionalities to export and import runtime changes made to an IMUNES experiment on Linux OSs.
Export functionality calculates the differences between the base Docker image and the actual container situation, and saves them to a specific folder in the filesystem.
Import functionality loads a saved configuration back to IMUNES.

I have written this snippet to allow students to save their work during the course of computer networks (laboratory), which I'm supporting as teaching lab assistant.

# Screenshot
![Screenshot](/screenshot.png?raw=true "Screenshot")

# Installation Guide

- Install pip requirements

```
# pip install -r requirements.txt
```

- Run setup

```
# python2 setup.py install
```

- Run with imunes-export with root or docker group's privileges (it uses docker's unix socket)

```
# imunes-export
```