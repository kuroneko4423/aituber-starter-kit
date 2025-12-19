"""VTube Studio avatar controller implementation."""

import logging
from pathlib import Path
from typing import Optional

from .base import BaseAvatarController

logger = logging.getLogger(__name__)


class VTubeStudioController(BaseAvatarController):
    """VTube Studio avatar controller using pyvts.

    This controller connects to VTube Studio via its WebSocket API
    to control Live2D model parameters, expressions, and hotkeys.

    Args:
        host: VTube Studio host address.
        port: VTube Studio API port.
        plugin_name: Name to identify this plugin.
        plugin_developer: Developer name for the plugin.
        token_path: Path to store authentication token.

    Note:
        VTube Studio must be running with API enabled.
        Go to Settings -> General Settings -> Start API

    Example:
        ```python
        controller = VTubeStudioController(
            host="localhost",
            port=8001,
            plugin_name="My AITuber"
        )
        await controller.connect()
        await controller.set_lip_sync(0.5)
        await controller.disconnect()
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8001,
        plugin_name: str = "AITuber Starter Kit",
        plugin_developer: str = "AITuber Community",
        token_path: str = "./vts_token.txt",
    ) -> None:
        """Initialize the VTube Studio controller.

        Args:
            host: VTube Studio host.
            port: API port number.
            plugin_name: Plugin identification name.
            plugin_developer: Developer name.
            token_path: Path for auth token file.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.plugin_info = {
            "plugin_name": plugin_name,
            "developer": plugin_developer,
            "authentication_token_path": token_path,
        }
        self._vts: Optional[object] = None
        self._custom_params: set[str] = set()
        logger.info(f"Initialized VTube Studio controller for {host}:{port}")

    async def connect(self) -> None:
        """Connect to VTube Studio.

        This will authenticate with VTube Studio and create
        custom parameters for lip sync.

        Raises:
            ImportError: If pyvts is not installed.
            ConnectionError: If connection fails.
        """
        if self._is_connected:
            logger.warning("Already connected to VTube Studio")
            return

        try:
            import pyvts
        except ImportError as e:
            raise ImportError(
                "pyvts is required for VTube Studio integration. "
                "Install with: pip install pyvts"
            ) from e

        try:
            self._vts = pyvts.vts(plugin_info=self.plugin_info)

            await self._vts.connect()  # type: ignore
            logger.info("Connected to VTube Studio WebSocket")

            # Authenticate
            await self._vts.request_authenticate_token()  # type: ignore
            await self._vts.request_authenticate()  # type: ignore
            logger.info("Authenticated with VTube Studio")

            # Create custom parameter for lip sync
            await self._create_custom_parameter(
                "AITuberMouthOpen", default=0.0, min_val=0.0, max_val=1.0
            )

            self._is_connected = True
            logger.info("VTube Studio controller ready")

        except Exception as e:
            self._vts = None
            raise ConnectionError(f"Failed to connect to VTube Studio: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from VTube Studio."""
        if self._vts:
            try:
                await self._vts.close()  # type: ignore
            except Exception as e:
                logger.warning(f"Error closing VTube Studio connection: {e}")
            self._vts = None

        self._is_connected = False
        self._custom_params.clear()
        logger.info("Disconnected from VTube Studio")

    async def _create_custom_parameter(
        self,
        name: str,
        default: float,
        min_val: float,
        max_val: float,
    ) -> None:
        """Create a custom parameter in VTube Studio.

        Args:
            name: Parameter name.
            default: Default value.
            min_val: Minimum value.
            max_val: Maximum value.
        """
        if not self._vts:
            raise RuntimeError("Not connected to VTube Studio")

        if name in self._custom_params:
            return

        try:
            request = self._vts.vts_request.requestCustomParameter(  # type: ignore
                parameter_name=name,
                default_value=default,
                min_value=min_val,
                max_value=max_val,
            )
            await self._vts.request(request)  # type: ignore
            self._custom_params.add(name)
            logger.debug(f"Created custom parameter: {name}")
        except Exception as e:
            # Parameter might already exist
            logger.debug(f"Custom parameter {name} may already exist: {e}")
            self._custom_params.add(name)

    async def set_parameter(self, name: str, value: float) -> None:
        """Set a model parameter value.

        Args:
            name: Parameter name.
            value: Parameter value.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._vts:
            raise RuntimeError("Not connected to VTube Studio")

        try:
            request = self._vts.vts_request.requestSetParameterValue(  # type: ignore
                parameter=name,
                value=value,
            )
            await self._vts.request(request)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to set parameter {name}: {e}")
            raise

    async def set_lip_sync(self, value: float) -> None:
        """Set lip sync (mouth open) value.

        Args:
            value: Mouth open value (0.0=closed, 1.0=fully open).
        """
        # Clamp value to valid range
        value = max(0.0, min(1.0, value))
        await self.set_parameter("AITuberMouthOpen", value)

    async def set_expression(self, expression_name: str) -> None:
        """Set avatar expression by triggering a hotkey.

        Args:
            expression_name: Name of the expression/hotkey.
        """
        await self.trigger_hotkey(expression_name)

    async def trigger_hotkey(self, hotkey_id: str) -> None:
        """Trigger a VTube Studio hotkey.

        Args:
            hotkey_id: ID or name of the hotkey.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._vts:
            raise RuntimeError("Not connected to VTube Studio")

        try:
            request = self._vts.vts_request.requestTriggerHotKey(hotkey_id)  # type: ignore
            await self._vts.request(request)  # type: ignore
            logger.debug(f"Triggered hotkey: {hotkey_id}")
        except Exception as e:
            logger.error(f"Failed to trigger hotkey {hotkey_id}: {e}")
            raise

    async def get_available_hotkeys(self) -> list[dict]:
        """Get list of available hotkeys.

        Returns:
            List of hotkey dictionaries with id and name.
        """
        if not self._vts:
            raise RuntimeError("Not connected to VTube Studio")

        try:
            request = self._vts.vts_request.requestHotKeyList()  # type: ignore
            response = await self._vts.request(request)  # type: ignore
            return response.get("data", {}).get("availableHotkeys", [])
        except Exception as e:
            logger.error(f"Failed to get hotkeys: {e}")
            return []

    async def get_available_parameters(self) -> list[dict]:
        """Get list of available model parameters.

        Returns:
            List of parameter dictionaries.
        """
        if not self._vts:
            raise RuntimeError("Not connected to VTube Studio")

        try:
            # Get input parameters
            request = self._vts.vts_request.requestInputParameterList()  # type: ignore
            response = await self._vts.request(request)  # type: ignore
            return response.get("data", {}).get("defaultParameters", [])
        except Exception as e:
            logger.error(f"Failed to get parameters: {e}")
            return []

    async def get_current_model(self) -> Optional[dict]:
        """Get information about the currently loaded model.

        Returns:
            Model info dictionary or None.
        """
        if not self._vts:
            raise RuntimeError("Not connected to VTube Studio")

        try:
            request = self._vts.vts_request.requestCurrentModel()  # type: ignore
            response = await self._vts.request(request)  # type: ignore
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Failed to get current model: {e}")
            return None
