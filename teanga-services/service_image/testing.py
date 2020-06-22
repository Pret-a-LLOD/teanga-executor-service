import docker
import subprocess
c = docker.DockerClient(base_url='unix://var/run/docker.sock', timeout=10)
image_name = "ubuntu:latest"
'''ctr = c.containers.run(image_name,
      command="bash -c ' for((i=1;i<=10;i+=2)); do echo Welcome $i            times; sleep 1; done'", detach=True)
logs = ctr.logs(stream=True)
print([tags for a in c.images.list() for tags in  a.tags ])
'''
subprocess.call("docker run -v /Users/kdu/projects/teanga_backend/service_image:/app -t servicetest bash /app/service.sh", shell=True)
