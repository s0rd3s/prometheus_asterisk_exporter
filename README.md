# Asterisk Prometheus Exporter

A Python-based Prometheus exporter for Asterisk metrics.

## Overview

This is a Prometheus exporter for Asterisk, written in Python. It collects metrics from Asterisk and exposes them in a format compatible with Prometheus.

## Important Note for Asterisk 18+ Users

If you're using **Asterisk 18 or later**, you should consider using the built-in [`res_prometheus`](https://docs.asterisk.org/Latest_API/API_Documentation/Module_Configuration/res_prometheus/) module instead.

**Important limitation**: If you're using the `res_sip` module (like me), `res_prometheus` won't work as it depends on the `res_pjsip` module.

## Dependencies

- Python 3
- pip (Python package manager)
- `prometheus_client` pip package

Install the required Python module:
```bash
pip install prometheus_client
```
## Systemd Unit
If you consider using my unit template - first you should create tmpfiles.d configuration:

```bash
# Create tmpfiles.d configuration
sudo tee /etc/tmpfiles.d/asterisk_exporter.conf > /dev/null <<EOF
d /var/run/asterisk_exporter 0755 asterisk asterisk -
EOF

# Create the directory
sudo systemd-tmpfiles --create /etc/tmpfiles.d/asterisk_exporter.conf
```
# Metrics
```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 329.0
python_gc_objects_collected_total{generation="1"} 33.0
python_gc_objects_collected_total{generation="2"} 0.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 45.0
python_gc_collections_total{generation="1"} 4.0
python_gc_collections_total{generation="2"} 0.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="8",patchlevel="10",version="3.8.10"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 1.79154944e+08
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 2.0942848e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.74437580165e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 175.5
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 6.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1024.0
# HELP asterisk_total_active_channels Total current active channels
# TYPE asterisk_total_active_channels gauge
asterisk_total_active_channels{host="server",type="active channels"} 0.0
# HELP asterisk_total_active_calls Total current active calls
# TYPE asterisk_total_active_calls gauge
asterisk_total_active_calls{host="server",type="active calls"} 0.0
# HELP asterisk_total_calls_processed Total current calls processed
# TYPE asterisk_total_calls_processed gauge
asterisk_total_calls_processed{host="server",type="calls processed"} 0.0
# HELP asterisk_system_uptime_seconds System uptime in seconds
# TYPE asterisk_system_uptime_seconds gauge
asterisk_system_uptime_seconds{host="server",type="system uptime seconds"} 0
# HELP asterisk_last_reload_seconds Seconds since last reload
# TYPE asterisk_last_reload_seconds gauge
asterisk_last_reload_seconds{host="server",type="last reload seconds"} 0
# HELP asterisk_total_sip_peers Total SIP peers
# TYPE asterisk_total_sip_peers gauge
asterisk_total_sip_peers{host="server",type="total sip peers"} 3.0
# HELP asterisk_total_monitored_online Total monitored online peers
# TYPE asterisk_total_monitored_online gauge
asterisk_total_monitored_online{host="server",type="total monitored online"} 2.0
# HELP asterisk_total_monitored_offline Total monitored offline peers
# TYPE asterisk_total_monitored_offline gauge
asterisk_total_monitored_offline{host="server",type="total monitored_offline"} 1.0
# HELP asterisk_total_unmonitored_online Total unmonitored online peers
# TYPE asterisk_total_unmonitored_online gauge
asterisk_total_unmonitored_online{host="server",type="total unmonitored_online"} 0.0
# HELP asterisk_total_unmonitored_offline Total unmonitored offline peers
# TYPE asterisk_total_unmonitored_offline gauge
asterisk_total_unmonitored_offline{host="server",type="total unmonitored offline"} 0.0
# HELP asterisk_total_threads Total threads listed
# TYPE asterisk_total_threads gauge
asterisk_total_threads{host="server",type="total threads listed"} 6.0
# HELP asterisk_total_sip_status_unknown Total SIP peers with unknown status
# TYPE asterisk_total_sip_status_unknown gauge
asterisk_total_sip_status_unknown{host="server",type="total sip status unknown"} 1.0
# HELP asterisk_total_sip_status_qualified Total SIP peers with qualified status
# TYPE asterisk_total_sip_status_qualified gauge
asterisk_total_sip_status_qualified{host="server",type="total sip status qualified"} 1.0
# HELP asterisk_sip_peer_status Status of SIP peer (1=OK, 0=not OK)
# TYPE asterisk_sip_peer_status gauge
asterisk_sip_peer_status{host="server",peer_host="1.1.1.2",peer_name="1900"} 1.0
asterisk_sip_peer_status{host="server",peer_host="10.1.1.1",peer_name="Internal"} 1.0
# HELP asterisk_sip_peer_latency_ms SIP peer latency in milliseconds
# TYPE asterisk_sip_peer_latency_ms gauge
asterisk_sip_peer_latency_ms{host="server",peer_host="1.1.1.2",peer_name="1900"} 8.0
asterisk_sip_peer_latency_ms{host="server",peer_host="10.1.1.1",peer_name="Internal"} 1.0
# HELP asterisk_sip_peer_port SIP peer port number
# TYPE asterisk_sip_peer_port gauge
asterisk_sip_peer_port{host="server",peer_host="1.1.1.2",peer_name="1900"} 5060.0
asterisk_sip_peer_port{host="server",peer_host="10.1.1.1",peer_name="Internal"} 5060.0
```

# Verify Exporter is Running

```bash
curl http://localhost:9255/metrics
```
You should see your Asterisk metrics in Prometheus format.