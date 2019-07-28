import json
import logging
import os
import re
import time
import typing
import bs4
import requests


log = logging.getLogger("N-Hentai")


def grab_galleries(galleries: typing.List[int] = None) -> None:
    if not galleries:
        return None

    # Fake User-Agent, pretend as Chrome 75
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/75.0.3770.142 Safari/537.36"
    }

    image_type_mapping: dict = {"j": ".jpg", "p": ".png", "b": ".bmp", "s": ".svg", "g": ".gif"}

    gallery_base_url: str = "https://nhentai.net/g/"
    image_base_url: str = "https://i.nhentai.net/galleries/"

    # Gallery loop in
    for gallery in galleries:
        gallery_url = "".join([gallery_base_url, str(gallery), "/"])
        title: str = ""
        meta_data: dict = dict()
        log.info(f"Download gallery {gallery} HTML Page from {gallery_url}")

        discard = False

        # Grab gallery main page
        status: int = 999  # dummy 999 http status
        retries: int = 0
        while not status == 200:
            response = requests.get(gallery_url, headers=headers)
            status = response.status_code
            if status != 200:
                retries += 1
                if retries > 3:
                    discard = True
                    break
                log.warning(f"HTTP_STATUS: {status}. Gallery {gallery} HTML page failed to download. "
                            f"Retry in 1 seconds. Retries: {retries}/3")
                time.sleep(1)
            else:
                soup = bs4.BeautifulSoup(response.text, "lxml")
                meta_data = json.loads(soup.select("script")[2].text[31:-22])
                if meta_data["title"]["japanese"]:
                    title = "_".join([str(gallery).zfill(10), meta_data["title"]["japanese"]])
                else:
                    title = "_".join([str(gallery).zfill(10), meta_data["title"]["english"]])

                # escape invalid filename chars
                title = re.sub("\\*", "＊", title)
                title = re.sub("\\|", "｜", title)
                title = re.sub("\\\\", "＼", title)
                title = re.sub("\"", "＂", title)
                title = re.sub("<", "＜", title)
                title = re.sub(">", "＞", title)
                title = re.sub("\\?", "？", title)
                title = re.sub("/", "／", title)
                title = re.sub("\t", "", title)
                title = re.sub("\r", "", title)
                title = re.sub("\n", "", title)

                if os.path.isdir(title) and os.path.exists(title):
                    log.warning(f"HTTP_STATUS: {status}. Gallery {gallery} {title} already exist."
                                f" Discard this gallery. {gallery_url}, {os.path.isdir(title)} {os.path.exists(title)}")
                    discard = True
                else:
                    log.info(f"Create DIR: {gallery} {title}")
                    os.mkdir(title)
                    with open("/".join([title, "metadata.json"]), "w", encoding="utf-8") as file:
                        file.write(json.dumps(meta_data, ensure_ascii=False))
                    break

        if not discard:
            pages: int = meta_data["num_pages"]

            log.info(f"Download gallery {gallery} ({pages} pages): {title} {gallery_url}")

            # Grab images of the gallery
            for index, page in enumerate(range(1, pages + 1)):
                image_type: str = meta_data["images"]["pages"][index]["t"]
                media_id = meta_data["media_id"]
                file_name: str = "".join([str(page), image_type_mapping[image_type]])
                image_url: str = "".join([image_base_url, media_id, "/", file_name])
                log.debug(f"Download {gallery} page {page}/{pages} from {image_url}")
                status = 999  # dummy 999 http status
                retries = 0
                while status != 200:
                    response = requests.get(image_url, headers=headers)
                    status = response.status_code
                    if status != 200:
                        retries += 1
                        if retries > 3:
                            break
                        log.warning(
                            f"HTTP_STATUS: {status}. Image {file_name} in {title} failed to download. "
                            f"Retries {retries}/3 {image_url}")
                        time.sleep(1)
                    else:
                        with open("/".join([title, file_name]), "wb") as file:
                            for chunk in response.iter_content(chunk_size=512*1024):
                                file.write(chunk)
