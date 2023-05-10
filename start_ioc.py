#!/usr/bin/env python3
import logging
import sys
import time
import asyncio

from caproto import ChannelType
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


log = logging.getLogger(__name__)


position_names = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"]


class RobotIOC(PVGroup):
    busy = pvproperty(value=False, doc="If the robot is busy.", read_only=True)
    sample = pvproperty(value='unknown', record='mbbi', 
                        enum_strings=("unknown", "empty", *position_names),
                        dtype=ChannelType.ENUM,
                        doc="The current sample on the sample stage.", )

    @sample.putter
    async def sample(self, instance, value):
        await self.busy.write(True)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.move_sample, value)
        await self.busy.write(False)
    
    def move_sample(self, value):
        log.info(f"Moving robot to {value}.")
        # Move the robot here
        time.sleep(5)
        

def main():
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='25idAustin:',
        desc='Run an IOC that operates the sample changing robot.')

    # Instantiate the IOC, assigning a prefix for the PV names.
    ioc = RobotIOC(**ioc_options)

    # Run IOC.
    run(ioc.pvdb, **run_options)


if __name__ == '__main__':
    sys.exit(main())
