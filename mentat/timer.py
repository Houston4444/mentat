import logging
import time
from typing import TYPE_CHECKING

from .config import MAINLOOP_PERIOD, MAINLOOP_PERIOD_NS

if TYPE_CHECKING:
    from engine import Engine


class Timer():

    logger = logging.getLogger(__name__)

    def __init__(self, engine: 'Engine'):

        self.engine = engine
        self.start_time = self.engine.current_time
        self.tempo = self.engine.tempo
        self.end_time = self.start_time
        self.is_beat_waiting = False

    def reset(self):
        """
        Called when the timer's scene is restarted
        """
        self.start_time = self.engine.current_time
        self.tempo = self.engine.tempo
        self.end_time = self.start_time
        self.is_beat_waiting = False

    def update_tempo(self):
        """
        Called when the engine's tempo has changed
        """

        new_tempo = self.engine.tempo

        if self.is_beat_waiting:
            """
            If we're currently waiting a beat-based duration,
            we need to adjust the end time
            """
            remaining_time = self.end_time - self.engine.current_time
            tempo_ratio = new_tempo / self.tempo
            self.end_time = self.engine.current_time + remaining_time / tempo_ratio

        self.tempo = new_tempo

    def wait(self, duration, mode):
        """
        wait for a given amount of time in beats or seconds
        """
        if mode[0] == 'b':
            duration = duration * 60. / self.tempo
            duration *= 1000000000 # s to ns
        elif mode[0] == 's':
            duration *= 1000000000 # s to ns
        elif mode == 'ns':
            pass
        else:
            self.logger.error('unrecognized mode "%s" for wait()' % mode)
            return

        self.end_time = self.start_time + duration

        if mode[0] == 'b':
            self.is_beat_waiting = True

        while self.engine.current_time < self.end_time - MAINLOOP_PERIOD_NS:
            time.sleep(MAINLOOP_PERIOD)

        self.is_beat_waiting = False

        self.start_time = self.end_time


    def get_current_beat(self, beat_div=1.0) -> int:
        """
        get engine's current beat
        """
        current_beat = 0
        map_length = len(self.engine.tempo_map)

        for i in range(map_length):
            _time, _tempo, _cycle = self.engine.tempo_map[i]

            if i == map_length - 1:
                elapsed_time = self.engine.current_time - _time
            else:
                next_time, next_tempo, next_cycle = self.engine.tempo_map[i + 1]
                elapsed_time = next_time - _time

            elapsed_beats = elapsed_time / 1000000000 / 60 * _tempo
            current_beat += elapsed_beats

        return int(current_beat)

    def wait_next_beat(self, beat_div=1.0):
        """
        wait until current beat changes
        """
        start_beat = self.get_current_beat(beat_div)
        while start_beat == self.get_current_beat(beat_div):
            time.sleep(MAINLOOP_PERIOD)

        self.start_time = self.engine.current_time

    def get_current_cycle(self):
        """
        get engine's current cycle
        """
        current_cycle = 0
        map_length = len(self.engine.tempo_map)

        for i in range(map_length):
            _time, _tempo, _cycle = self.engine.tempo_map[i]

            if i == map_length - 1:
                elapsed_time = self.engine.current_time - _time
            else:
                next_time, next_tempo, next_cycle = self.engine.tempo_map[i + 1]
                elapsed_time = next_time - _time

            elapsed_beats = elapsed_time / 1000000000 / 60 * _tempo
            current_cycle += elapsed_beats / _cycle

        return int(current_cycle)
        

    def wait_next_cycle(self):
        """
        wait until current cycle changes
        """
        start_cycle = self.get_current_cycle()
        while start_cycle == self.get_current_cycle():
            time.sleep(MAINLOOP_PERIOD)

        self.start_time = self.engine.current_time
