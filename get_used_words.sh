#!/bin/bash

curl -s https://www.stadafa.com/2021/09/every-worlde-word-so-far-updated-daily.html \
    | grep -Po '^<p>[0-9]+\. \K(\w+?) '\
    | tr 'A-Z' 'a-z'
