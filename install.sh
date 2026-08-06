
sudo apt update
sudo apt install -y python3
sudo apt install -y python3-pip

python3 -m pip install . --break-system-packages --ignore-installed urllib3

