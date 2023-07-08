#!/bin/bash

diff -uNp . /media/phil/CIRCUITPY/ | filterdiff -i '*.py' | lsdiff