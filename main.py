import logging
import multiprocessing
import sys
import typing
from crawler import grab_galleries


LOG_LEVEL = logging.INFO
FORMAT = "[%(asctime)s] Level: %(levelname)-8s File: %(filename)-20s Func: %(funcName)-30s Line: %(lineno)-10d" \
         " Message: %(message)s"
LOG_FORMAT = logging.Formatter(FORMAT)
log = logging.getLogger("N-Hentai")
log.setLevel(LOG_LEVEL)

# Add File Handler (log output to file)
# FH = logging.FileHandler(os.path.join('N-Hentai.log'))
# FH.setLevel(LOG_LEVEL)
# FH.setFormatter(LOG_FORMAT)
# log.addHandler(FH)

# Add Console Handler (log output to console)
CH = logging.StreamHandler(sys.stdout)
CH.setLevel(LOG_LEVEL)
CH.setFormatter(LOG_FORMAT)
log.addHandler(CH)


def arrange_galleries(galleries: str = "", total_threads: int = 1
                      ) -> typing.List[typing.List[int]]:
    job_list: typing.List[typing.List[int]] = [[] for _ in range(total_threads)]
    if not galleries:
        return job_list
    index_count = 0
    for chunk in galleries.split(","):
        if "-" not in chunk:
            job_list[index_count % total_threads].append(int(chunk))
            index_count += 1
        else:
            gallery_range = chunk.split("-")
            if len(gallery_range) == 2:
                start, stop = int(gallery_range[0]), int(gallery_range[1])
                if start <= stop:
                    for gallery in range(start, stop + 1, 1):
                        job_list[index_count % total_threads].append(gallery)
                        index_count += 1
                else:
                    for gallery in range(start, stop - 1, -1):
                        job_list[index_count % total_threads].append(gallery)
                        index_count += 1
            else:
                warn = f"Detect invalid input : {chunk}"
                log.warning(warn)
                raise ValueError(warn)
    return job_list


def main_multi() -> None:
    try:
        total_threads: int = int(input("Enter thread number : "))
        galleries: str = str(input("Enter galleries (e.g. 1-500,501,666,9487,1000-1450) : "))

        job_list: typing.List[typing.List[int]] = arrange_galleries(galleries=galleries,
                                                                    total_threads=total_threads)

        pool = multiprocessing.Pool(total_threads)
        pool.map(grab_galleries, job_list)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        exit(0)


def main() -> None:
    gallery_start: int = int(input("Start from album No. (include):"))
    gallery_end: int = int(input("Stop at album No. (include):"))

    worker_list: typing.List[int] = arrange_galleries(gallery_start, gallery_end, 1)[0]

    grab_galleries(worker_list)


if __name__ == "__main__":
    main_multi()
