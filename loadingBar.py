"""
Module for showing a loading bar in the console output
"""

import sys
import time


class LoadingBar():
    """
    This class creates a loading bar object
    """

    def __init__(self, incrementCount, updateInterval=1, width=50, fillString='=', displayIncrementCount=True):
        """

        :param incrementCount: Number of increments required to reach 100%
        :param updateInterval: The percent change required to update the status bar
        :param width: The width of the loading bar in characters
        :param fillString: The string to fill the loading bar with
        :param displayIncrementCount: Flag to determine if the the number of completed increments should be displayed
        """

        self.incrementCount = incrementCount
        self.updateInterval = updateInterval

        self.width = width

        self.fillString = fillString
        self.displayIncrementCount = displayIncrementCount

        self.currentIncrements = 0
        self.currentPercent = 0
        self.last = ''

    def update(self, increments=1):
        """
        Update the status bar by adding to the increment count

        :param increments: number of increments to add to the increment count
        """

        self.currentIncrements += increments
        percent = (float(self.currentIncrements) / self.incrementCount) * 100.0

        if (percent - self.currentPercent) > self.updateInterval or percent == 100:
            self.currentPercent += self.updateInterval
            if percent == 100:
                self.currentPercent = 100
            fillingStr = int(self.currentPercent * ((float(self.width) / len(self.fillString)) / 100.0)) * self.fillString
            percentStr = ' {0:d}% '.format(self.currentPercent) if percent != 100 else " COMPLETE "
            percentPos = (int(self.width) / 2) - (len(percentStr) / 2)
            fullFilling = fillingStr + ' ' * (int(self.width) - len(fillingStr))
            fullString = '[' + fullFilling[:int(percentPos)] + percentStr + fullFilling[int(percentPos + len(percentStr)):] + '] '
            self.last = fullString
            sys.stdout.write('\r{0}'.format(fullString))

        if self.displayIncrementCount:
            incrementString = '{0}/{1}'.format(self.currentIncrements, self.incrementCount)
            sys.stdout.write('\r{0}'.format(self.last + incrementString))

        if percent == 100:
            print('')

if __name__ == '__main__':
    sb = LoadingBar(100)
    for i in range(100):
        sb.update()
        time.sleep(.1)