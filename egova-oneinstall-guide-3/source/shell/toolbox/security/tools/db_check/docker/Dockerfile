FROM python:3.9-slim
# 设置时区
ENV TZ=Asia/Shanghai
# 设置 pip 使用国内镜像源
RUN mkdir -p /root/.pip && \
    echo "[global]\n\
timeout = 6000\n\
index-url = https://pypi.tuna.tsinghua.edu.cn/simple\n\
[install]\n\
trusted-host = pypi.tuna.tsinghua.edu.cn" > /root/.pip/pip.conf
RUN mkdir -p /egova
COPY yq /usr/bin/
COPY requirements.txt /egova
WORKDIR /egova
# 安装项目依赖
RUN  pip install --upgrade pip && \
pip install --no-cache-dir -r requirements.txt
COPY . /egova/db_check
WORKDIR /egova/db_check
CMD ["sh","/egova/db_check/check_safe_config.sh"]
