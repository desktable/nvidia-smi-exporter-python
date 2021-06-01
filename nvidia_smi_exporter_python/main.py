import asyncio
import os
import argparse

from aiohttp import web


async def handle(request):
    proc = await asyncio.create_subprocess_exec(
        "nvidia-smi",
        "--query-gpu=name,index,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used",
        "--format=csv,noheader,nounits",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise Exception(
            "\n".join(
                [
                    "Error running nvidia-smi:",
                    "stdout=" + stdout.decode("utf-8"),
                    "stderr=" + stderr.decode("utf-8"),
                ]
            )
        )
    output = []
    for line in stdout.decode("utf-8").strip().split("\n"):
        groups = line.split(",")
        name = groups[0].strip()
        index = int(groups[1].strip())
        temperature_gpu = int(groups[2].strip())
        utilization_gpu = int(groups[3].strip())
        utilization_memory = int(groups[4].strip())
        memory_total = int(groups[5].strip())
        memory_free = int(groups[6].strip())
        memory_used = int(groups[7].strip())
        tag = "{" + f'gpu="{name}[{index}]"' + "}"
        output.append(f"temperature_gpu{tag} {temperature_gpu}")
        output.append(f"utilization_gpu{tag} {utilization_gpu}")
        output.append(f"utilization_memory{tag} {utilization_memory}")
        output.append(f"memory_total{tag} {memory_total}")
        output.append(f"memory_free{tag} {memory_free}")
        output.append(f"memory_used{tag} {memory_used}")
    return web.Response(text="\n".join(output))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("-p", "--port", default=9101)
    args = parser.parse_args()

    app = web.Application()
    app.router.add_get("/metrics", handle)

    web.run_app(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
