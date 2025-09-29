import asyncio
import json
import platform
import psutil
import cpuinfo
import time
from typing import List, Optional

from pydantic import BaseModel, Field


"""
see https://stackoverflow.com/questions/69919970/no-module-named-distutils-util-but-distutils-is-installed
`distutils` was removed with py 3.12, that and we need to install setuptools to make GPUtils work.
"""


class SystemInfo(BaseModel):
    """The main model for our system information payload."""
    timestamp: int = Field(..., description="Time at which this data was captured")
    arch: str = Field(..., description="System architecture (e.g., x86_64, arm64).")
    os_name: str = Field(..., description="The name of the operating system (e.g., Windows, Ubuntu, macOS).")
    os_version: str = Field(..., description="The specific version of the operating system.")
    cpu: str = Field(..., description="The brand and model of the CPU.")
    memory_gb: float = Field(..., description="Total system RAM in GB.")
    gpus: List = Field([], description="A list of GPUs found in the system.")

def get_os_info() -> tuple[str, str]:
    """
    Gets the OS name and version in a platform-independent way.
    """
    system = platform.system()
    if system == "Windows":
        return "Windows", platform.version() 
    
    # highly doubt ill ever get it
    elif system == "Darwin":
        return "macOS", platform.mac_ver()[0]
    
    elif system == "Linux":
        try:
            import distro
            return distro.name(pretty=True), distro.version(pretty=True)
        
        except ImportError as e:
            print(f"OS DETECTION :: error => {e}")
            return "Linux", platform.release()
        
    return system, platform.release()

def get_gpu_info() -> List:
    """
    Gets GPU information using the GPUtil library.
    Returns an empty list if no GPUs are found or the library is not installed.
    """
    gpus = []
    try:
        import GPUtil
        for gpu in GPUtil.getGPUs():
            gpus.append(gpu.name)

    except (ImportError, Exception) as e:
        print(f"GPU DETECTION :: error => {e}")
        gpus.append("Not detected")

    return gpus

async def gather_system_info() -> SystemInfo:
    """
    Asynchronously gathers all system information and returns a Pydantic model.
    Note: The gathering functions themselves are blocking, but we wrap them
    in an async function for future compatibility with non-blocking I/O (like the API call).
    """
    print("Gathering system information...")
    os_name, os_version = get_os_info()
    
    payload_data = {
        "arch": platform.machine(),
        "os_name": os_name,
        "os_version": os_version,
        "cpu": cpuinfo.get_cpu_info().get("brand_raw", "Not detected"),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "gpus": get_gpu_info(),
        "timestamp": int(time.time())
    }
    
    return SystemInfo(**payload_data)

async def publish_to_api():
    pass # placeholder

async def main():
    system_info_model = await gather_system_info()
    print(system_info_model.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())