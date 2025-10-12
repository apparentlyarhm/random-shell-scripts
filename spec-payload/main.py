from datetime import datetime as dt
from typing import List
from pydantic import BaseModel, Field

import asyncio
import platform
import psutil
import cpuinfo
import time
import aiohttp
import dotenv
import os
import subprocess
import math

dotenv.load_dotenv(".env")

HOST = os.environ["HOST"]
API_KEY = os.environ["API_KEY"]

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

def get_os_info(system: str) -> tuple[str, str]:
    """
    Gets the OS name and version in a platform-independent way.
    """
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

def get_gpu_info(system: str) -> List:
    """
    Gets GPU information using the OS only. I think without drivers the OS will not report as expected.
    """
    gpus = []
    command = ""

    if system == "Windows":
        command = "wmic path win32_videocontroller get name"
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
        lines = output.strip().split('\n')
        # The first line is "Name", so we skip it.
        # Subsequent lines are the GPU names, with potential whitespace.
        for line in lines[1:]:
            gpu_name = line.strip()
            if gpu_name:
                gpus.append(gpu_name)
    
    elif system == "Linux":
        command = "lspci | grep VGA"
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
        
        for line in output.strip().split('\n'):
            if "VGA compatible controller" in line:
                # The name is typically after the colon, e.g.,
                # "01:00.0 VGA compatible controller: NVIDIA Corporation GP104 [GeForce GTX 1080]"
                # or 
                # "03:00.0 VGA compatible controller: Advanced Micro Devices, Inc. [AMD/ATI] Navi 44 [Radeon RX 9060 XT] (rev c0)"
                full_name = line.split(":", 2)[-1].strip()
                if "Advanced Micro Devices, Inc." in full_name:
                    gpus.append(full_name.replace("Advanced Micro Devices, Inc. [AMD/ATI]", "AMD"))

                else:
                    gpus.append(full_name)

    if not gpus:
        print(":: the platform isnt Linux/Win :: ")
        gpus.append("Not detected")
    
    return gpus

async def gather_system_info(system: str) -> SystemInfo: 
    """
    Asynchronously gathers all system information and returns a Pydantic model.
    Note: The gathering functions themselves are blocking, but we wrap them
    in an async function for future compatibility with non-blocking I/O (like the API call).
    """
    print("Gathering system information...")
    os_name, os_version = get_os_info(system)
    
    payload_data = {
        "arch": platform.machine(),
        "os_name": os_name,
        "os_version": os_version,
        "cpu": cpuinfo.get_cpu_info().get("brand_raw", "Not detected"),
        "memory_gb": math.floor(psutil.virtual_memory().total / (1000**3)),
        "gpus": get_gpu_info(system),
        "timestamp": int(time.time())
    }
    
    return SystemInfo(**payload_data)

async def publish_to_api(data: SystemInfo, host: str, key: str, retries: int, delay: int):

    async with aiohttp.ClientSession() as s:
        for attempt in range(retries):
            try:
                async with s.post(
                    url=f"{host}/report", 
                    json=data.model_dump(), 
                    headers={'X-API-KEY': key},
                    ) as r:
                    # there is nothing to process
                    r.raise_for_status()
                    print(f"Data sent for {dt.fromtimestamp(data.timestamp).strftime("%A, %d. %B %Y %I:%M%p")}")
                    break

            except aiohttp.ClientResponseError as e:

                if e.status == 429:
                    print("rate limited :: attempting again with backoff")
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                    else: 
                        print("Unrecoverable rate limtation..")
            
                else:
                    if e.status == 401:
                        print("Check api key")
                       
                    # any other error we will not do anything and (not)silently fail
                    print("Request failed.")
                    break

            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                print("host unreachable :: attempting again")

                if attempt < retries - 1:
                    await asyncio.sleep(delay * 2) 

                else:
                    print("All retries failed.")

async def main():
    system = platform.system()

    system_info_model = await gather_system_info(system)
    print(system_info_model.model_dump_json(indent=2))

    # await publish_to_api(system_info_model, HOST, API_KEY, 5, 2)


if __name__ == "__main__":
    asyncio.run(main())