import subprocess
import os

mp3_data = b"\xff\xfb\x90\x44\x00\x00\x00\x00" # Some garbage mp3 data, or better yet, I'll download a tiny real mp3
import urllib.request
urllib.request.urlretrieve("https://actions.google.com/sounds/v1/alarms/beep_short.ogg", "test.ogg") # Wait, MediaPlayer doesn't support OGG out of the box. Let's find an MP3.
