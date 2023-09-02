FROM python:3.11

# install libosmesa6 as recommended
# x11-xserver-utils provides xrandr
# see https://github.com/deepmind/pysc2/issues/202
RUN apt-get update \
  && apt-get install -y \
    x11-xserver-utils \
    libosmesa6 \
    python3-opencv \
    python3-numpy \
  && rm -rf /var/lib/apt/lists/*

RUN pip3 install burnysc2 six opencv-python pyqt5
