from __future__ import annotations

from typing import TYPE_CHECKING

from API.source.ap_interface.io.analog_io import AnalogIO
from API.source.ap_interface.io.digital_io import DigitalIO
from API.source.core.connection_state import (
    ConnectionState,
)

if TYPE_CHECKING:
    from logging import Logger

    from API.source.core.network.controller_socket import (
        Controller,
    )
    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )


class IO:
    """
    Класс для работы с входами/выходами контроллера робота.
    """

    digital: DigitalIO
    """Подкласс для работы с цифровыми входами/выходами."""
    analog: AnalogIO
    """Подкласс для работы с аналоговыми входами/выходами."""

    def __init__(
        self,
        controller: Controller,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        logger: Logger,
    ) -> None:
        self._connection_state = connection_state
        self.digital = DigitalIO(
            controller=controller,
            rtd_receiver=rtd_receiver,
            connection_state=connection_state,
            logger=logger,
        )
        self.analog = AnalogIO(
            controller=controller,
            rtd_receiver=rtd_receiver,
            connection_state=connection_state,
            logger=logger,
        )
