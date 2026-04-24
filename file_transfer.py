import paramiko

hostname = "18.216.229.209"
username = "ubuntu"  
key_path = "C:/Users/gugga/Downloads/key-instance.pem"

local_file = "C:/Users/gugga/OneDrive/Desktop/zip_files/sample.txt"
remote_file = "/home/ubuntu/sample.txt"

try:
    key = paramiko.RSAKey.from_private_key_file(key_path)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=hostname,
        username=username,
        pkey=key
    )
    print("Connected to EC2")
    sftp = ssh.open_sftp()
    sftp.put(local_file, remote_file)
    print("File transferred successfully!")

    sftp.close()
    ssh.close()

except Exception as e:
    print("Error:", str(e))