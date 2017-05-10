import logging
import os
import subprocess
import time
import unittest
from logging import DEBUG, StreamHandler

log = logging.getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
log.setLevel(DEBUG)
log.addHandler(handler)


class TestRedisHA(unittest.TestCase):
  wait = 60

  def _kubectl(self, command):
    return subprocess.run(
        ['kubectl', '-n', self._namespace] + command, stdout=subprocess.PIPE
    )

  def setUp(self):
    self._namespace = os.environ.get('KUBE_NAMESPACE', 'default')
    self._kubectl(['create', '-f', './example'])
    time.sleep(self.wait)

  def tearDown(self):
    self._kubectl(['delete', '-f', './example'])
    time.sleep(60)

  def _delete_pod(self, pod_name):
    self._kubectl(['delete', 'pod', pod_name])

  def assertPodPhase(self, pod_name, pod_phase):
    result = subprocess.run(
        ['test/script/check-pod-status', self._namespace, pod_name, pod_phase],
        stdout=subprocess.PIPE
    )
    self.assertEqual(0, result.returncode)

  def assertRedisCliResponce(self, command, responce, role='master'):
    result = subprocess.run(
        ['test/script/kube-redis-cli-{}'.format(role)] + command,
        stdout=subprocess.PIPE
    )
    self.assertEqual(responce, result.stdout)
    self.assertEqual(0, result.returncode)

  def assertRedisSlaveNum(self, num):
    result = subprocess.run(
        ['test/script/get-slave-ip'], stdout=subprocess.PIPE
    )
    self.assertEqual(num + 1, len(result.stdout.split(b'\n')))
    self.assertEqual(0, result.returncode)

  def assertRedisSentinelNum(self, num):
    result = subprocess.run(
        ['test/script/get-sentinel-ip'], stdout=subprocess.PIPE
    )
    self.assertEqual(num, len(result.stdout.split(b'\n')))
    self.assertEqual(0, result.returncode)

  def _scale(self, resource_name, num):
    self._kubectl(['scale', '--replicas={}'.format(num), resource_name])


class TestDeletePodRedisserver0AfterSettingValue(TestRedisHA):
  def test_delete_po_redisserver0_after_setting_value(self):
    self.assertRedisCliResponce(['set', 'foo', '"bar"'], b'OK\n')
    self.assertRedisCliResponce(['get', 'foo'], b'"bar"\n')
    self._delete_pod('redis-server-0')
    time.sleep(120)
    self.assertPodPhase('redis-server-0', 'Running')
    self.assertRedisCliResponce(['get', 'foo'], b'"bar"\n')


class TestSetGetDel(TestRedisHA):
  def test_set_get_del(self):
    self.assertRedisCliResponce(['set', 'foo', '"bar"'], b'OK\n')
    self.assertRedisCliResponce(['get', 'foo'], b'"bar"\n')
    self.assertRedisCliResponce(['del', 'foo'], b'1\n')
    self.assertRedisCliResponce(['get', 'foo'], b'\n')


class TestGetFromSlave(TestRedisHA):
  def test_get_from_slave(self):
    self.assertRedisCliResponce(['set', 'foo', '"bar"'], b'OK\n')
    self.assertRedisCliResponce(['get', 'foo'], b'"bar"\n', role='slave')


class TestDeletePodRedisserver0(TestRedisHA):
  def test_delete_po_redisserver0(self):
    self._delete_pod('redis-server-0')
    time.sleep(120)
    self.assertPodPhase('redis-server-0', 'Running')


class TestDeletePodRedissentinel0(TestRedisHA):
  def test_delete_po_redissentinel0(self):
    self._delete_pod('redis-sentinel-0')
    time.sleep(120)
    self.assertPodPhase('redis-sentinel-0', 'Running')


class TestScaleOutInServer(TestRedisHA):
  def test_scale_out_in_server(self):
    self._scale('statefulset/redis-server', 5)
    time.sleep(60)
    for x in range(5):
      self.assertPodPhase('redis-server-{}'.format(x), 'Running')
    self._scale('statefulset/redis-server', 3)
    time.sleep(60)
    for x in range(3):
      self.assertPodPhase('redis-server-{}'.format(x), 'Running')
    self.assertRedisSlaveNum(2)


# Scale-in of Sentinels doesn't reset Sentinels #11
# https://github.com/tarosky/k8s-redis-ha/issues/11
class TestScaleOutInSentinel(TestRedisHA):
  def test_scale_out_in_sentinel(self):
    self._scale('statefulset/redis-sentinel', 5)
    time.sleep(60)
    for x in range(5):
      self.assertPodPhase('redis-sentinel-{}'.format(x), 'Running')
    self._scale('statefulset/redis-sentinel', 3)
    time.sleep(120)
    for x in range(3):
      self.assertPodPhase('redis-sentinel-{}'.format(x), 'Running')
    self.assertRedisSentinelNum(3)


# # This is a test case to delete a Pod with Master
# # before Sentinel starts a majority. As a result, deadlock occurs.
# # However, considering the property of replication
# # it is appropriate for deadlock to occur.
# # Therefore, this is not an appropriate test case.
# class TestDeletePodRedisserver0OnInit(TestRedisHA):
#   wait = 20
#
#   def test_delete_po_redisserver0_on_init(self):
#     self._delete_pod('redis-server-0')
#     time.sleep(120)
#     self.assertPodPhase('redis-server-0', 'Running')

if __name__ == '__main__':
  unittest.main()
