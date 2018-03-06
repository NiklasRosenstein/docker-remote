# The MIT License (MIT)
#
# Copyright (c) 2018 Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""
This module generates random project names.
"""

import random

adjectives = """
best
better
big
certain
clear
different
early
easy
economic
federal
free
full
good
great
hard
high
important
international
large
late
little
local
long
low
major
new
old
only
other
political
possible
public
real
recent
right
small
social
special
strong
sure
true
whole
young
""".strip().split('\n')

nouns = """
area
book
business
case
company
country
day
eye
fact
group
hand
home
job
life
lot
money
month
mother
night
number
part
place
point
problem
program
question
right
room
school
state
story
student
study
system
thing
time
water
way
week
word
work
world
year
""".strip().split('\n')

def namegen(sep='_'):
  return random.choice(adjectives) + sep + random.choice(nouns)


if __name__ == '__main__':
  print(namegen())
