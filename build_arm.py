import os
os.system('docker buildx build . --platform linux/amd64 -t motgama')
os.system('docker-compose up')