
"""
.. module:: bosefeatureversion
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the BoseMultiRoomVersions class which describes the various feature versions
               associated with a bose player.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2024, Myron W Walker"
__credits__ = []

from automojo.networking.protocols.upnp.manufacturers.bose.description.bosefeatureversion import BoseFeatureVersion


class BoseMultiRoomVersions:

    def __init__(self, audio_control: BoseFeatureVersion, audio_payload: BoseFeatureVersion, clock_sync: BoseFeatureVersion,
                 now_playing: BoseFeatureVersion, playback_request: BoseFeatureVersion, zone_control: BoseFeatureVersion):
        self._audio_control = audio_control
        self._audio_payload = audio_payload
        self._clock_sync = clock_sync
        self._now_playing = now_playing
        self._playback_request = playback_request
        self._zone_control = zone_control
        return

    @property
    def audio_control(self) -> BoseFeatureVersion:
        return self._audio_control
    
    @property
    def audio_payload(self) -> BoseFeatureVersion:
        return self._audio_payload
    
    @property
    def clock_sync(self) -> BoseFeatureVersion:
        return self._clock_sync
    
    @property
    def now_playing(self) -> BoseFeatureVersion:
        return self._now_playing
    
    @property
    def playback_request(self) -> BoseFeatureVersion:
        return self._playback_request
    
    @property
    def zone_control(self) -> BoseFeatureVersion:
        return self._zone_control

