import asyncio
import logging
import re
import subprocess

from exceptions import DownloadFailedException
from interfaces import Downloader

logger = logging.getLogger(__name__)


class Wget(Downloader):
    TIMEOUT = 2 * 60

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def get_output_directory_name(self, url):
        match = re.search("^((http|https)://)?(www\\.)?(?P<website_name>[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]+)*)\\.[a-zA-Z0-9_-]+$", url)
        website_name = match.group("website_name")
        return f"{self.output_dir}/{website_name}"

    async def download(self, url: str) -> str:
        output_directory = self.get_output_directory_name(url)
        try:
            subprocess.run(
                [
                    "wget",
                    "--timeout=5",
                    "--tries=3",
                    "-U"
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
                    "-E",
                    "-H",
                    "-p",
                    "-nd",
                    "--save-headers",
                    "-P",
                    output_directory,
                    url,
                ], timeout=self.TIMEOUT)
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout in fetch {url}")
            raise DownloadFailedException

        return output_directory


class AsyncWget(Wget):

    async def download(self, url: str) -> str:
        output_directory = self.get_output_directory_name(url)
        proc = await asyncio.create_subprocess_exec(
            "wget",
            "--timeout=5",
            "--tries=3",
            "-U"
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "-E",
            "-H",
            "-p",
            "-nd",
            "--save-headers",
            "-P",
            output_directory,
            url,
        )
        logger.info(f"Download started for {url} with process {proc.pid}")

        try:
            await asyncio.wait_for(proc.wait(), timeout=self.TIMEOUT)
        except asyncio.TimeoutError:
            logger.error(f"Timeout in fetch {url}")
            raise DownloadFailedException

        logger.info(f"Download finished for {url} with process {proc.pid}")
        return output_directory
