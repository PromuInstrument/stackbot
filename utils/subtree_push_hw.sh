#!/bin/sh
cd "$(dirname "$0")"/..

git subtree push --prefix ScopeFoundryHW/$1/ https://edbarnard@github.com/ScopeFoundry/HW_$1.git master