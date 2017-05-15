# Kubernetes Redis with High Availability

Redis Images and Samples in this project are implemented using the latest features of Kubernetes:

* StatefulSet
* Init Container

# Requirements

* Kubernetes 1.6 cluster
* Redis 3.2

# Quick Start

If you already have a Kubernetes cluster, you can deploy High Availability Redis using the following command:

```console
$ kubectl create -f example/
service "redis-sentinel" created
statefulset "redis-sentinel" created
service "redis-server" created
statefulset "redis-server" created
pod "console" created
```

## Accessing Redis

You can access Redis server using `console` pod:

```console
$ kubectl exec -ti console -- /bin/bash
root@console:# export MASTER_IP="$(redis-cli -h redis-sentinel -p 26379 sentinel get-master-addr-by-name mymaster | head -1)"
root@console:# export SERVER_PASS="_redis-server._tcp.redis-server.default.svc.cluster.local"
root@console:# redis-cli -h "${MASTER_IP}" -a "${SERVER_PASS}" set foo bar
OK
root@console:# redis-cli -h redis-server -a "${SERVER_PASS}" get foo
bar
```

The passowrd is necessary for preventing independent Redis clusters from merging together in some circumstances.

## Scale Up and Down

With `tarosky/k8s-redis-ha`, you can scale up/down Redis servers and Redis sentinels like the normal Deployment resources:

```console
$ kubectl scale --replicas=5 statefulset/redis-sentinel
statefulset "redis-sentinel" scaled
$ kubectl scale --replicas=5 statefulset/redis-server
statefulset "redis-server" scaled
```

After these scale up/down, the expected number of available slaves in the Redis set are reset automatically.

# Sample Code in Python

```console
$ kubectl exec -ti console -- ipython
```

```python
In [1]: from redis import StrictRedis

In [2]: from redis.sentinel import Sentinel

In [3]: sentinel = Sentinel([
   ...:         ('redis-sentinel-0.redis-sentinel.default.svc.cluster.local', 26379),
   ...:         ('redis-sentinel-1.redis-sentinel.default.svc.cluster.local', 26379),
   ...:         ('redis-sentinel-2.redis-sentinel.default.svc.cluster.local', 26379)
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

# Running the Test Script

```console
$ pyvenv .venv
$ source .venv/bin/activate
$ pip install -r test/requirements.txt
```

You can run the test command using the following command:

```console
$ KUBE_NAMESPACE='{{Your name space}}' nosetests test/test.py
```
