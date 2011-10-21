import os
import random
import pygame
import settings

class Music:
    MUSIC_FINISHED = 59859
    def __init__(self):
        self.tracks = os.listdir(settings.MUSIC_DIR)
        if settings.MUSIC_SHUFFLE:
            random.shuffle(self.tracks)
        self.track = 0

        pygame.mixer.music.set_endevent(Music.MUSIC_FINISHED)

    def start_playing(self):
        self.next_track()

    def stop_playing(self):
        pygame.mixer.music.stop()

    def next_track(self):
        pygame.mixer.music.load(settings.MUSIC_DIR + self.tracks[self.track])
        pygame.mixer.music.play()

        self.track += 1
        if self.track >= self.tracks:
            self.track = 0

    def handle_event(self, event):
        if event.type == Music.MUSIC_FINISHED:
            self.next_track()
