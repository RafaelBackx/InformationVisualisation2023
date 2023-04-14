#!/bin/bash

DIR="./"

for file in "$DIR"/*
do
    mapshaper $file -simplify 10% -o "$file"_opt.json
done