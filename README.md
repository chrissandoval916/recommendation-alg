## To build image

```
docker build -t recomalg .
```

## To run container

_Note: run in powershell_
```
docker run -d --name recomalg --volume ${PWD}/src:/data recomalg:latest
docker exec -it recomalg bash
```