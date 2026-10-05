# This is an auto generated Dockerfile for ros:ros-core
# generated from docker_images_ros2/create_ros_core_image.Dockerfile.em
FROM ubuntu:focal

# setup timezone
RUN echo 'Etc/UTC' > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && \
    apt-get install -q -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

# install packages
RUN apt-get update && apt-get install -q -y --no-install-recommends \
    ca-certificates \
    curl \
    dirmngr \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*


# setup keys
RUN set -eux; \
       key='4B63CF8FDE49746E98FA01DDAD19BAB3CBF125EA'; \
       export GNUPGHOME="$(mktemp -d)"; \
       gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "$key"; \
       mkdir -p /usr/share/keyrings; \
       gpg --batch --export "$key" > /usr/share/keyrings/ros2-snapshots-archive-keyring.gpg; \
       gpgconf --kill all; \
       rm -rf "$GNUPGHOME"

# setup sources.list
RUN echo "deb [ signed-by=/usr/share/keyrings/ros2-snapshots-archive-keyring.gpg ] http://snapshots.ros.org/foxy/final/ubuntu focal main" > /etc/apt/sources.list.d/ros2-snapshots.list

# setup environment
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

ENV ROS_DISTRO=foxy

    
# install bootstrap tools
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    git \
    python3-colcon-common-extensions \
    python3-colcon-mixin \
    python3-rosdep \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# bootstrap rosdep
RUN rosdep init && \
  rosdep update --rosdistro $ROS_DISTRO

# setup colcon mixin and metadata
RUN colcon mixin add default \
      https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml && \
    colcon mixin update && \
    colcon metadata add default \
      https://raw.githubusercontent.com/colcon/colcon-metadata-repository/master/index.yaml && \
    colcon metadata update   

    
# install ros2 packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-foxy-desktop=0.9.2-1* \
    && rm -rf /var/lib/apt/lists/*  



# 设置上海时区
RUN ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone


# 安装OS基础软件
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    vim \
    usbutils \
    pciutils \
    iputils-ping \
    net-tools \
    iproute2 \
    tree \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*


# 安装 Rosmaster_Lib 驱动库
COPY py_install_V3.3.9.zip /tmp/

RUN cd /tmp && \
    unzip py_install_V3.3.9.zip && \
    cd py_install && \
    python3 setup.py install && \
    cd / && \
    rm -rf /tmp/py_install /tmp/py_install_V3.3.9.zip

# 安装 Speech_Lib 驱动库
COPY py_install_V0.0.1.zip /tmp/

RUN cd /tmp && \
    unzip py_install_V0.0.1.zip && \
    cd py_install && \
    python3 setup.py install && \
    cd / && \
    rm -rf /tmp/py_install /tmp/py_install_V0.0.1.zip

# 安装用于串口通信（Serial）的 Python 库
RUN python3 -m pip install --no-cache-dir \
    pyserial

# 安装 opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*
    
# 安装 numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*
    
# 安装 jupyterlab
RUN python3 -m pip install --no-cache-dir \
    pyzmq==25.0.0 \
    jupyterlab==3.6.1
    
# 安装 ipywidgets，用于jupyter网页
RUN python3 -m pip install --no-cache-dir \
    ipywidgets

# 安装 jupyterlab_widgets，用于jupyter网页
RUN python3 -m pip install --no-cache-dir \
    jupyterlab_widgets

# 安装 qrcode pyzbar
RUN python3 -m pip install --no-cache-dir \
    qrcode \
    pyzbar

# 安装 libzbar-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 pcl-tools 用于 pcl_viewer 命令
RUN apt-get update && apt-get install -y --no-install-recommends \
    pcl-tools \
    && rm -rf /var/lib/apt/lists/*

# 安装 libuvc
RUN apt-get update && apt-get install -y --no-install-recommends \
    libuvc-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 dlib
RUN python3 -m pip install --no-cache-dir \
    dlib==19.24.9
    
# 安装 libgoogle-glog-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgoogle-glog-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 flask
RUN python3 -m pip install --no-cache-dir \
    flask

# 安装 python3-gevent
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-gevent \
    && rm -rf /var/lib/apt/lists/*   

# 安装 pykdl
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pykdl \
    && rm -rf /var/lib/apt/lists/* 

# 安装 libusb-1.0-0-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0-0-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 nlohmann-json3-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*
    
# 安装 python3-tk
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# 安装 mediapipe，并去掉它拉上来的 OpenCV 5，继续用 apt 的 python3-opencv
RUN python3 -m pip install --no-cache-dir \
    "mediapipe==0.10.9" \
    && python3 -m pip uninstall -y opencv-contrib-python

# 安装 XXX




# 安装 ros2 功能包
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-foxy-xacro \
    ros-foxy-joint-state-publisher \
    ros-foxy-joint-state-publisher-gui \
    ros-foxy-imu-filter-madgwick \
    ros-foxy-robot-localization \
    ros-foxy-nav2-map-server \
    ros-foxy-cartographer-ros \
    ros-foxy-camera-calibration* \
    ros-foxy-usb-cam \
    ros-foxy-async-web-server-cpp \
    ros-foxy-rosbridge-suite \
    ros-foxy-rosbridge-test-msgs \
    ros-foxy-navigation2 \
    ros-foxy-nav2-bringup \
    ros-foxy-libg2o \
    ros-foxy-image-publisher \
    ros-foxy-pcl-ros \
    ros-foxy-octomap-rviz-plugins \
    ros-foxy-octomap-server \
    ros-foxy-rtabmap-ros \
    && rm -rf /var/lib/apt/lists/* 



# 添加环境变量
RUN echo "source /opt/ros/foxy/setup.bash" >> /root/.bashrc

# setup entrypoint
COPY ./ros_entrypoint.sh /
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]

