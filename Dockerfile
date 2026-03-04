FROM python:3

ENV DEBIAN_FRONTEND=noninteractive

# install libosmesa6 as recommended
# x11-xserver-utils provides xrandr
# see https://github.com/deepmind/pysc2/issues/202
RUN  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt-get update \
  && apt-get install -y \
    x11-xserver-utils \
    libosmesa6 \
    python3-opencv \
    python3-numpy

RUN pip3 install burnysc2 six opencv-python websockets
