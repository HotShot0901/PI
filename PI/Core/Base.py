from ..Instrumentation import Instrumentor, InstrumentationTimer

PI_VERSION       : str   = "0.8.4.dev"
PI_VERSION_TUPLE : tuple = (0,8,4)

PI_LATEST_UPDATE: str = """
    x.x.0
    Added Texture Support in 3D Renderer

    x.x.1
    Major refactoring in file structure

    x.x.2
    Added Light Casters

    x.x.3
    Added Support for multiple Light casters in one Scene
"""

#-------------------------------------------------------------------
# Platforms
SUPPORTED_PLATFORMS = ["Windows"]           # Currently only supports Windows
CURRENT_PLATFORM = SUPPORTED_PLATFORMS[0]
#-------------------------------------------------------------------

#-------------------------------------------------------------------
# To turn on and off certain features
PI_CONFIGS : tuple = ("DEBUG", "NO_INSTRUMENTATION", "RELEASE", "RELEASE_NO_IMGUI")
PI_CONFIG  : str   = PI_CONFIGS[0]

PI_DEBUG           : bool
PI_LOGGING         : bool
PI_INSTRUMENTATION : bool
PI_IMGUI           : bool

PI_V_SYNC: bool = True

# Full DEBUG Configuration
if PI_CONFIG == "DEBUG":
    PI_DEBUG   : bool = True
    PI_LOGGING : bool = True
    PI_IMGUI   : bool = True
    PI_INSTRUMENTATION: bool = True

# NO_INSTRUMENTATION Configuration
if PI_CONFIG == "NO_INSTRUMENTATION":
    PI_DEBUG   : bool = True
    PI_LOGGING : bool = True
    PI_IMGUI   : bool = True
    PI_INSTRUMENTATION: bool = False

# Strips all debugging features
if PI_CONFIG == "RELEASE":
    PI_DEBUG   : bool = False
    PI_LOGGING : bool = False
    PI_IMGUI   : bool = True
    PI_INSTRUMENTATION: bool = False

# Strips all debugging features and ImGui
if PI_CONFIG == "RELEASE_NO_IMGUI":
    PI_DEBUG   : bool = False
    PI_LOGGING : bool = False
    PI_IMGUI   : bool = False
    PI_INSTRUMENTATION: bool = False

try:
    # if Python is able to import this it means the docking branch is enabled
    from imgui import CONFIG_DOCKING_ENABLE
except ImportError:
    from ..Logging.logger import PI_CORE_ASSERT
    PI_CORE_ASSERT(False, "ImGui-Docking branch is not present.")
# -------------------------------------------------------------------

#-------------------------------------------------------------------
# Instrumentation
def EmptyFunc(name: str=""):
    pass

PI_INSTRUMENTATION_BEGIN_SESSION = EmptyFunc
PI_INSTRUMENTATION_END_SESSION   = EmptyFunc
PI_TIMER = EmptyFunc

if PI_INSTRUMENTATION:
    def _BeginSession(name: str) -> None:
        Instrumentor.Get().BeginSession(name)
        
    def _EndSession() -> None:
        Instrumentor.Get().EndSession()

    def _Timer(name: str) -> InstrumentationTimer:
        return InstrumentationTimer(name)

    PI_INSTRUMENTATION_BEGIN_SESSION = _BeginSession
    PI_INSTRUMENTATION_END_SESSION   = _EndSession
    PI_TIMER = _Timer
#-------------------------------------------------------------------

#-------------------------------------------------------------------
# Other basic utility functions and classes
import numpy as _np

class Random:
    __slots__ = "__BaseAPI"

    def __init__(self) -> None:
        Random.__BaseAPI = _np.random

    @staticmethod
    def Init() -> None:
        Random.__BaseAPI = _np.random

    @staticmethod
    def Random(size=None) -> float:
        return Random.__BaseAPI.random(size)

    @staticmethod
    def RandomInt(begin: int, end: int) -> int:
        return Random.__BaseAPI.randint(begin, end)

    @staticmethod
    def GenerateName(base: str="") -> str:
        prevNames = []
        while True:
            name = "{}{}".format(base, Random.RandomInt(0, 10000))
            if name not in prevNames:
                prevNames.append(name)
                yield name
#-------------------------------------------------------------------
