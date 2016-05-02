## Docker Image Usage
since lain uses docker, we encounter docker in docker in this image, so we need to mount $(which docker) and /var/run/docker.sock to the image,
docker commands used in lain also needs a place to put temporary data, it's /tmp, but since docker is run on host, the output will be put in host's
/tmp, but the container also needs to access the temporary place, so we need to `-v /tmp:/tmp`
/lain/app is the default work directory, if you mount {directory with lain.yaml} to other directories, you need to specify it with --yaml

`docker run -v $(which docker):/usr/local/bin/docker -v /var/run/docker.sock:/var/run/docker.sock -v /tmp:/tmp -v {directory with lain.yaml}:/lain/app changcheng/lain-sdk -h` for more help

## Test
use [py.test](http://pytest.org/latest/) for testing

tests are under `tests` directory

in the same directory as this file, run `py.test` for testing

## Configuration

### PRIVATE_DOCKER_REGISTRY

1. set private_docker_registry in /etc/lain/lain.conf.yaml
