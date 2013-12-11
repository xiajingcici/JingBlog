JingBlog
========

Please view on 

https://jingblogost.appspot.com/

http://stackoverflow.com/questions/8634700/python-indentationerror-unexpected-indent

Spent 2 hours to debug this issue!!!!!

Run your program with

python -t script.py
This will warn you if you have mixed tabs and spaces.

On *nix systems, you can see where the tabs are by running

cat -A script.py
and you can automatically convert tabs to 4 spaces with the command

expand -t 4 script.py > fixed_script.py
PS. Be sure to use a programming editor (e.g. emacs, vim), not a word processor, when programming. You won't get this problem with a programming editor.