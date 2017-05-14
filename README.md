# Kubernetes Redis with High Availability

Kubernetes Redis Images and Samples implemented using the latest features:

* StatefulSet
* Init Container


# Requirements

* Kubernetes 1.6.* cluster
* Redis 3.2


# Quick Start

If you have already a Kubernetes cluster, you can deploy High Availability Redis using the command below:

```console
$ kubectl create -f example/
service "redis-sentinel" created
statefulset "redis-sentinel" created
service "redis-server" created
statefulset "redis-server" created
pod "console" created
```


## Accessing redis

You can access Redis through the pod "console" using `kubectl exec -ti console -- /bin/bash`:

```console
$ # Log in console Pod
$ kubectl exec -ti console -- /bin/bash
root@console:# export MASTER_IP="$(redis-cli -h redis-sentinel -p 26379 sentinel get-master-addr-by-name mymaster | head -1)"
root@console:# export SERVER_PASS="_redis-server._tcp.redis-server.default.svc.cluster.local"
root@console:# redis-cli -h "${MASTER_IP}" -a "${SERVER_PASS}" set foo bar # set foo=bar 
OK
root@console:# redis-cli -h redis-server -a "${SERVER_PASS}" get foo 
bar
```

If you aren't on 'default' namespace, please replace default in `$SERVER_PASS` with your namespace:

```console
root@console:# export SERVER_PASS="_redis-server._tcp.redis-server.abcde.svc.cluster.local"
```


## Scale in out

`tarosky/k8s-redis-ha` has abilities to scale in and scale out.
You can check this feature below:

```console
$ kubectl scale --replicas=5 statefulset/redis-sentinel
statefulset "redis-sentinel" scaled
$ kubectl scale --replicas=5 statefulset/redis-server
statefulset "redis-server" scaled
```


# Sample code in Python to use High Availability Redis 

Here is the sample code on ipython which access Redis through redis-py.
To run the code, you must install [`redis-py`](https://pypi.python.org/pypi/redis) and ipython on your application pods.
In example, a console pod is prepared, so you can start by command below: 

```console
$ kubectl exec -ti console -- ipython
```

```python
In [1]: from redis import StrictRedis

In [2]: from redis.sentinel import Sentinel

In [3]: sentinel = Sentinel([
   ...:         ('redis-sentinel-0.redis-sentinel.oshita.svc.cluster.local', 26379),
   ...:         ('redis-sentinel-1.redis-sentinel.oshita.svc.cluster.local', 26379),
   ...:         ('redis-sentinel-2.redis-sentinel.oshita.svc.cluster.local', 26379)
   ...:     ], socket_timeout=0.1
   ...: )

In [4]: master = sentinel.master_for(
   ...:     'mymaster',
   ...:     password='_redis-server._tcp.redis-server.default.svc.cluster.local',
   ...:     socket_timeout=0.1
   ...: )

In [5]: slave = sentinel.slave_for(
   ...:     'mymaster',
   ...:     password='_redis-server._tcp.redis-server.default.svc.cluster.local',
   ...:     socket_timeout=0.1
   ...: )

In [6]: master.set('foo', 'bar')
Out[6]: True

In [7]: slave.get('foo')
Out[7]: b'bar'
```

# Running test script

To check if Pods and others generated from `example/` and `images/` have High Availability, Test script is in `test/`.
Test script requires Python virtual environment to run it.
Here is an example how to build test environment.

```console
$ pyvenv .venv
$ source .venv/bin/activate
$ pip install -r test/requirements.txt
```

You can run test command using command below.

```console
$ KUBE_NAMESPACE='{{Your name space}}' nosetests test/test.py
```
