# Persistent Windows Python Backdoor
###### Proof of Concept Python persistence kit

This project started when I was looking at ways of gaining persistence with
Python-based malware. I didn't find much information about gaining it on modern
Windows boxes. There are the obvious ways we all know and love; but those are
too well known to be effective nowadays. So I decided to create the Python
Infection Engine (PIE) with a goal of parasitic infection on Python scripts.

While I was creating PIE it soon became apparent that a delivery system was also
needed. That is when 'snekhunt' was born. Yes, it's quite hacky script; it was
written on the fly with little to no planning and 'just had to work'. It may be
something that needs adjusting per system but it's achieved its goal for me. It
may be something I revisit later to clean it up.

PIE can be a little unstable. There are some scripts it completely fails to
infect. Usually this is to do with the import section of the host script being
a little more 'involved' than your average script. It's not something I'm
looking to work on right now. I think a better workaround would be to limit the
scope of snekhunt to pick out more specific/well-used libraries.

[Accompanying article](https://redskal.medium.com/python-malware-persistence-with-windows-65eb7ed02334)