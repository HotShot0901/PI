import os, sys, pathlib
import importlib
import inspect
import debugpy
from typing import Dict, List, Any, Type, Callable

from ..Logging    import PI_CLIENT_ERROR, DebugConsole
from .FileWatcher import *

class Script: ...

class Module:
    __AllScripts: Dict[str, Script]

    def __init__(self, path: str):
        self.Path = path
        self.Error = False

        path = path.replace('\\', '/')
        if path.startswith('./'): path = path[2:]
        path = path.split('/')
        
        self.Name = path[-1].replace(".py", '')
        
        sys.path.append(str(pathlib.Path(self.Path).absolute().parent))
        try: self.Module = importlib.reload(importlib.import_module(self.Name))
        except Exception as _:
            PI_CLIENT_ERROR("Error loading module\n{}", _)
            self.Error = True
        sys.path.pop()

        self.__ScanForScripts()

    def __ScanForScripts(self) -> None:
        if self.Error:
            self.__AllScripts = {}
            return

        scripts = [
            s for s in self.Module.__dir__()
            if (not s.startswith("_") and inspect.isclass(self.Module.__dict__[s]))
        ]
        self.__AllScripts = { s: Script(self, s) for s in scripts }

    @property
    def AllScripts(self) -> Dict[str, Script]: return self.__AllScripts

    def AllScriptsExtending(self, baseClass: Type) -> Dict[str, Script]:
        return { name: script for name, script in self.AllScripts.items() if script.Extends == baseClass }
        
class Script:
    def __init__(self, module: Module, scriptName: str, mustExtend: Type=object) -> None:
        self.Bound = False

        self.Module = module
        self.Name = scriptName

        self.Script = script = self.Module.Module.__dict__.get(scriptName, None)
        self.Extends = self.Script.__base__

        if script is None: raise ImportError(
            "Cannot find script named: {} in module: {}".format(self.Name, self.Module.Name)
        )

        if not issubclass(script, mustExtend): raise ImportError(
            "Script named: {} does not extend {}".format(self.Name, mustExtend.__name__)
        )

    def Bind(self, *initArgs: List[Any]) -> None:
        self.Object = self.Script(*initArgs)
        self.Bound = True

    def BindFunctions(self, *funcNames: List[str]) -> None:
        if not self.Bound: raise ImportError("Script not bound")

        for funcName in funcNames:
            try: func = getattr(self.Object, funcName)
            except: func = False

            if not func: raise ImportError(
                "Script named: {} does not have Function named {}".format(self.Name, funcName)
            )

            self.__setattr__(funcName, func)

    @property
    def ExternalFunctions(self) -> List[str]:
        if not self.Bound: raise ImportError("Script not bound")
        return [
            var for var in dir(self.Object)
            if not var.startswith('_') and isinstance(getattr(self.Object, var), Callable)
        ]

    @property
    def ExternalVariables(self) -> Dict[str, Any]:
        if not self.Bound: raise ImportError("Script not bound")

        variables = {}
        # Annotations
        try:
            for var, varType in self.Object.__annotations__.items():
                variables[var] = varType()
        except: pass

        # Defined variables
        for var in dir(self.Object):
            if not var.startswith('_') and not isinstance(getattr(self.Object, var), Callable):
                variables[var] = getattr(self.Object, var)

        return variables

    def SetVariables(self, variables: Dict[str, Any]):
        for name, value in variables.items():
            if name in self.ExternalVariables.keys(): setattr(self.Object, name, value)

class ScriptingEngine:
    DIR: str
    Modules: Dict[str, Module] = {}

    _DirWatcher: DirectoryWatcher

    class EventHandler(FileSystemEventHandler):
        @staticmethod
        def OnCreated  (_) -> None: ScriptingEngine.ScanForModules()
        @staticmethod
        def OnModified (_) -> None: ScriptingEngine.ScanForModules()
        @staticmethod
        def OnDeleted  (_) -> None: ScriptingEngine.ScanForModules()
        @staticmethod
        def OnMoved    (_) -> None: ScriptingEngine.ScanForModules()

    class Debugger:
        Running = False

        @staticmethod
        def Init(pythonLoc: str) -> int:
            if ScriptingEngine.Debugger.Running: return

            try: debugpy.configure(python=pythonLoc)
            except Exception as _: return False

            ScriptingEngine.Debugger.Running = True
            return True

        @staticmethod
        def Shutdown() -> None: ScriptingEngine.Debugger.Running = False

        @staticmethod
        def Listen(port):
            if not ScriptingEngine.Debugger.Running: return

            try: debugpy.listen(port)
            except Exception as _:
                ScriptingEngine.Debugger.Running = False
                return False

            return True

        @staticmethod
        def IsClientConnected() -> bool: return debugpy.is_client_connected()

        @staticmethod
        def AttachToDebugger() -> None:
            if not ScriptingEngine.Debugger.Running: return
            if not debugpy.is_client_connected(): debugpy.wait_for_client()

    @staticmethod
    def Init(scriptDir: str) -> None:
        ScriptingEngine.DIR = scriptDir
        ScriptingEngine.ScanForModules()

        ScriptingEngine._DirWatcher = DirectoryWatcher(pathlib.Path(scriptDir), ScriptingEngine.EventHandler)
        ScriptingEngine._DirWatcher.Start()
        
        DebugConsole.Init()

    @staticmethod
    def Shutdown() -> None:
        ScriptingEngine._DirWatcher.Stop()
        ScriptingEngine.Debugger.Shutdown()

    @staticmethod
    def ScanForModules() -> Dict[str, Module]:
        ScriptingEngine.Modules = {}

        def _ScanForModules(path: str, nodes: List[str], allModules: List[str], filter: str='.py'):
            nodes.append(path)

            try: dirs = os.listdir(path)
            except NotADirectoryError as _:
                if path.endswith(filter): allModules.append(path)
                return

            for dir in dirs: _ScanForModules(f"{path}\\{dir}", nodes, allModules)

            nodes.pop()

        allModules = []
        _ScanForModules(ScriptingEngine.DIR, [], allModules)

        for module in allModules:
            module = Module(module)
            ScriptingEngine.Modules[module.Name] = module

        return ScriptingEngine.Modules

    @staticmethod
    def Load(filepath) -> Module:
        module = ScriptingEngine.Modules.get(filepath, False)
        if not module: ScriptingEngine.Modules[filepath] = module = Module(filepath)
        return module
