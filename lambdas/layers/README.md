# Create a Lambda Layer for Notifications

### 1. Start a container with an Amazon Linux 2023 image

```bash
docker run -it amazonlinux:2023 /bin/bash
```

### 2. Update packages and install necessary tools

```bash
dnf update -y
dnf install -y   gcc   make   zlib-devel   libffi-devel   bzip2-devel   xz-devel   wget   openssl-devel   tar   readline-devel xz
```

### 3. Create installation directory and download Python 3.13.0

```bash
cd /usr/src
wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tar.xz
tar -xf Python-3.13.0.tar.xz
cd Python-3.13.0
```

### 4. Configure and install Python

```bash
./configure --enable-optimizations
make -j$(nproc) # Compiles Python using multiple cores
make altinstall # Installs Python without overwriting the system's python3 (python3.9)
```

### 5. Verify installed version

```bash
python3.13 --version
```

### 6. Create folder structure

```bash
mkdir -p /layer/python
```

### 7. Install necessary libraries not included in AWS Lambda

```bash
python3.13 -m pip install requests==2.32.4 -t /layer/python
```

### 8. Copy binaries outside the container and create the zip file

Without closing the current terminal where the container is running, open another terminal and execute:

```bash
docker ps # get the container id
docker cp {contenedor_id}:/layer/python ./python # docker cp ecc3ef0670b4:/layer/python ./python
```

Go to the location of the `python` folder obtained from the container to compress it:

```bash
zip -r requests.zip python
unzip -l requests.zip | head -n 10 # Verify its structure
# Expected result:
#   Length      Date    Time    Name
# ---------  ---------- -----   ----
#         0  2025-07-01 16:33   python/
#         0  2025-07-01 16:33   python/urllib3/
#     17295  2025-07-01 16:33   python/urllib3/_collections.py
#         0  2025-07-01 16:33   python/urllib3/contrib/
#         0  2025-07-01 16:33   python/urllib3/contrib/__init__.py
#      7549  2025-07-01 16:33   python/urllib3/contrib/socks.py
#         0  2025-07-01 16:33   python/urllib3/contrib/emscripten/
```

Copy the obtained zip file to `lambdas/layers`