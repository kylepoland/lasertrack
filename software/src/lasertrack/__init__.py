"""LaserTrack box software.

The daemon (`lasertrack run`) owns input: it watches the NFC reader, and when a
cartridge goes in it stops FieldStation42 and plays the cartridge's Plex media
with its own mpv. Pulling the cartridge reports the position to Plex and hands
the screen back to FieldStation42.
"""

__version__ = "0.1.0"
