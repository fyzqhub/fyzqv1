ARG BASE_IMAGE=ghcr.io/autowarefoundation/autoware:universe-devel-cuda-jazzy
FROM ${BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
# Ubuntu 24.04 的 pip 默认拒绝装到系统环境，这里统一放开
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# 以 root 安装
USER root

# 设置上海时区
RUN ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 安装 ros-jazzy-desktop，包含 rviz2、rqt 等
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-desktop \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*  

# 安装 ros2 功能包
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-imu-filter-madgwick \
    ros-jazzy-robot-localization \
    ros-jazzy-nav2-map-server \
    ros-jazzy-cartographer-ros \
    ros-jazzy-camera-calibration \
    ros-jazzy-usb-cam \
    ros-jazzy-async-web-server-cpp \
    ros-jazzy-rosbridge-suite \
    ros-jazzy-rosbridge-test-msgs \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-libg2o \
    ros-jazzy-image-publisher \
    ros-jazzy-pcl-ros \
    ros-jazzy-octomap-rviz-plugins \
    ros-jazzy-octomap-server \
    ros-jazzy-rtabmap-ros \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 

# 安装基础软件
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    vim \
    usbutils \
    pciutils \
    iputils-ping \
    net-tools \
    tree \
    unzip \
    # python 库，优先 apt 安装
    python3-serial \
    python3-qrcode \
    python3-pyzbar \
    python3-flask \
    python3-gevent \
    python3-pykdl \
    python3-tk \
    # 系统库和工具
    libzbar-dev \
    pcl-tools \
    libuvc-dev \
    libgoogle-glog-dev \
    libusb-1.0-0-dev \
    nlohmann-json3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
# 安装 Rosmaster_Lib 驱动库
COPY Rosmaster_Lib_3.3.9 /tmp/Rosmaster_Lib_3.3.9
RUN python3 -m pip install /tmp/Rosmaster_Lib_3.3.9 && \
    rm -rf /tmp/Rosmaster_Lib_3.3.9

# 安装 Speech_Lib 驱动库
COPY Speech_Lib_0.0.1 /tmp/Speech_Lib_0.0.1
RUN python3 -m pip install /tmp/Speech_Lib_0.0.1 && \
    rm -rf /tmp/Speech_Lib_0.0.1

# pip 安装 apt 里没有的
# Jupyter 一套（apt 无 jupyterlab，三者版本相互依赖，统一 pip）
RUN python3 -m pip install \
    jupyterlab \
    ipywidgets \
    jupyterlab_widgets

# 安装 dlib
RUN python3 -m pip install \
    dlib

# 安装 mediapipe，加 numpy<2 防止覆盖 apt 的 numpy 1.26.4，并去掉它拉来的 opencv-contrib，继续用 apt 的 python3-opencv
RUN python3 -m pip install \
    mediapipe "numpy<2" \
    && python3 -m pip uninstall -y opencv-contrib-python

# 构建时检测 numpy/opencv 没被 pip 包弄坏
RUN python3 -c "import numpy, cv2, serial, mediapipe; print(numpy.__version__, cv2.__version__)"

# 新增安装 XXX


# 添加环境变量
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /opt/autoware/setup.bash" >> /root/.bashrc

# setup entrypoint
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

