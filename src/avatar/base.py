"""Abstract base class for avatar controllers."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseAvatarController(ABC):
    """Abstract base class for avatar controllers.

    This class defines the interface for controlling avatar software
    like VTube Studio, Live2D Viewer, etc.

    Example:
        ```python
        class MyAvatarController(BaseAvatarController):
            async def connect(self) -> None:
                # Connect to avatar software
                pass

            async def disconnect(self) -> None:
                # Disconnect
                pass

            async def set_parameter(self, name: str, value: float) -> None:
                # Set a parameter value
                pass
        ```
    """

    def __init__(self) -> None:
        """Initialize the avatar controller."""
        self._is_connected: bool = False

    @property
    def is_connected(self) -> bool:
        """Check if connected to avatar software.

        Returns:
            True if connected, False otherwise.
        """
        return self._is_connected

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the avatar control software.

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the avatar control software."""
        pass

    @abstractmethod
    async def set_parameter(self, name: str, value: float) -> None:
        """Set a model parameter value.

        Args:
            name: Parameter name.
            value: Parameter value (typically 0.0-1.0).

        Raises:
            RuntimeError: If not connected.
        """
        pass

    @abstractmethod
    async def set_expression(self, expression_name: str) -> None:
        """Set the avatar's expression.

        Args:
            expression_name: Name of the expression to activate.

        Raises:
            RuntimeError: If not connected.
        """
        pass

    @abstractmethod
    async def trigger_hotkey(self, hotkey_id: str) -> None:
        """Trigger a hotkey action.

        Args:
            hotkey_id: ID or name of the hotkey to trigger.

        Raises:
            RuntimeError: If not connected.
        """
        pass

    async def set_lip_sync(self, value: float) -> None:
        """Set lip sync mouth open value.

        This is a convenience method that sets the mouth open parameter.
        Override in subclasses if the parameter name differs.

        Args:
            value: Mouth open value (0.0=closed, 1.0=fully open).
        """
        await self.set_parameter("MouthOpen", value)

    async def get_available_parameters(self) -> list[dict]:
        """Get list of available model parameters.

        Returns:
            List of parameter info dictionaries.
        """
        return []

    async def get_available_hotkeys(self) -> list[dict]:
        """Get list of available hotkeys.

        Returns:
            List of hotkey info dictionaries.
        """
        return []
