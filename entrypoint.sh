#!/bin/bash
set -e

# 失败只提示，不让容器启动失败
try_set() {
    "$@" >/dev/null 2>&1 ||
        echo "[entrypoint] WARN: failed: $*" >&2
}

# 开启回环网卡 lo 的多播功能：镜像里的 Cyclone DDS 把通信固定在 lo 上，节点发现需要它
# 需要 privileged；在 host 网络下改的是宿主机的 lo
# Enable multicast on loopback so DDS discovery works when pinned to lo
try_set ip link set lo multicast on

# Apply system-wide network tuning for DDS (needs --privileged or --cap-add=NET_ADMIN)
# https://autowarefoundation.github.io/autoware-documentation/main/installation/additional-settings-for-developers/network-configuration/dds-settings/#tune-system-wide-network-settings
# DDS 网络调优，来自 Autoware 官方文档，需要 privileged；host 网络下改的是宿主机，重启恢复
# 接收缓冲区上限：Cyclone 配置要求 ≥10MB，系统默认值太小会丢包
try_set sysctl -w net.core.rmem_max=2147483647
# IP 分片重组：缩短残片保留时间、扩大重组内存，主要用于将来走真实网卡的大消息
try_set sysctl -w net.ipv4.ipfrag_time=3
try_set sysctl -w net.ipv4.ipfrag_high_thresh=134217728

# 加载 ROS 2 环境，结尾的 "--" 表示不把脚本参数传给 setup.bash
# shellcheck source=/dev/null
source "/opt/ros/${ROS_DISTRO}/setup.bash" --

# 加载预编译的 Autoware，官方 devel 镜像默认不加载，这里改为只要文件存在就加载
if [ -f /opt/autoware/setup.bash ]; then
    # shellcheck source=/dev/null
    source /opt/autoware/setup.bash
fi

# 用传入的命令替换当前进程，保证信号和退出码正常传递
exec "$@"
