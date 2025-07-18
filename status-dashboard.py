from flask import Flask, render_template_string, send_from_directory, jsonify
import subprocess
import psutil
import os
import json
import time
import socket

app = Flask(__name__)

@app.route('/ddclient.png')
def ddclient_logo():
    return send_from_directory('/srv/www', 'ddclient.png')

@app.route('/unbound.png')
def unbound_logo():
    return send_from_directory('/srv/www', 'unbound.png')

@app.route('/wg.png')
def wg_logo():
    return send_from_directory('/srv/www', 'wg.png')

@app.route('/ethernet.png')
def ethernet_logo():
    return send_from_directory('/srv/www', 'ethernet.png')

@app.route('/grass.jpg')
def grass_logo():
    return send_from_directory('/srv/www', 'minecraft.png')

@app.route('/kavita.png')
def kavita_logo():
    return send_from_directory('/srv/www', 'kavita.png')

@app.route('/trilium.png')
def trilium_logo():
    return send_from_directory('/srv/www', 'trilium.png')

@app.route('/audiobookshelf.png')
def audiobookshelf_logo():
    return send_from_directory('/srv/www', 'audiobookshelf.png')

def is_port_open(host, port, timeout=1.5, udp=False):
    try:
        if udp:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            try:
                # Send a dummy UDP packet
                sock.sendto(b"", (host, port))
                # Try to receive; if port is open but nothing is listening, ICMP error may be returned, else timeout
                sock.recvfrom(1024)
            except socket.timeout:
                pass  # timeout is expected if port is open but not replying
            except Exception:
                sock.close()
                return False
            sock.close()
            return True
        else:
            with socket.create_connection((host, port), timeout=timeout):
                return True
    except Exception:
        return False

def collect_dashboard_data():
    services = []
    # Systemd-checked services, except VPN and Trilium
    for label, icon, service, display, url in [
        ('DDNS', 'ddclient.png', 'ddclient', 'Active', 'https://ap.www.namecheap.com/Domains/DomainControlPanel/rej1.me/advancedns'),
        ('DNS', 'unbound.png', 'unbound', 'Active', None),
    ]:
        status = subprocess.getoutput(f'systemctl is-active {service}').strip()
        active = (status == 'active')
        color = '#3fa94d' if active else '#c23b22'
        text = 'Online' if active else 'Offline'
        services.append({'label': label, 'icon': icon, 'color': color, 'url': url, 'text': text})

    # VPN: check if UDP port 4500 is open on the VPN endpoint
    vpn_host = "optiplex.lan"
    vpn_port = 4500
    vpn_active = is_port_open(vpn_host, vpn_port, udp=True)
    vpn_color = '#3fa94d' if vpn_active else '#c23b22'
    vpn_text = 'Online' if vpn_active else 'Offline'
    services.append({'label': 'VPN', 'icon': 'wg.png', 'color': vpn_color, 'url': 'https://optiplex.lan:9090/network', 'text': vpn_text})

    # Trilium: check if port 8080 is open, not systemd
    trilium_host = "optiplex.lan"
    trilium_port = 8080
    trilium_online = is_port_open(trilium_host, trilium_port)
    trilium_color = '#3fa94d' if trilium_online else '#c23b22'
    trilium_text = 'Online' if trilium_online else 'Offline'
    services.append({'label': 'Trilium', 'icon': 'trilium.png', 'color': trilium_color, 'url': 'http://optiplex.lan:8080/', 'text': trilium_text})

    # Kavita: check by port, not systemd
    kavita_host = "optiplex.lan"
    kavita_port = 5000
    kavita_online = is_port_open(kavita_host, kavita_port)
    kavita_color = '#3fa94d' if kavita_online else '#c23b22'
    kavita_text = 'Online' if kavita_online else 'Offline'
    services.append({'label': 'Kavita', 'icon': 'kavita.png', 'color': kavita_color, 'url': 'http://optiplex.lan:5000/', 'text': kavita_text})

    # Audiobookshelf: check by port
    audiobookshelf_host = "optiplex.lan"
    audiobookshelf_port = 13378
    audiobookshelf_online = is_port_open(audiobookshelf_host, audiobookshelf_port)
    audiobookshelf_color = '#3fa94d' if audiobookshelf_online else '#c23b22'
    audiobookshelf_text = 'Online' if audiobookshelf_online else 'Offline'
    services.append({
        'label': 'ABS',
        'icon': 'audiobookshelf.png',
        'color': audiobookshelf_color,
        'url': 'http://optiplex.lan:13378/',
        'text': audiobookshelf_text
    })

    # Ethernet
    try:
        carrier = subprocess.getoutput("ip link show enp2s0 | grep -q 'state UP' && echo 1 || echo 0").strip()
        eth_active = (carrier == "1")
    except Exception:
        eth_active = False
    eth_color = '#3fa94d' if eth_active else '#c23b22'
    eth_text = 'Online' if eth_active else 'Offline'
    services.append({'label': 'Ethernet', 'icon': 'ethernet.png', 'color': eth_color, 'url': 'http://192.168.0.1/', 'text': eth_text})

    # ATM10 Minecraft server (port check)
    mc_host = "rej1.me"
    mc_port = 25565
    mc_online = is_port_open(mc_host, mc_port)
    mc_color = '#3fa94d' if mc_online else '#c23b22'
    mc_text = 'Online' if mc_online else 'Offline'
    services.append({'label': 'ATM10', 'icon': 'grass.jpg', 'color': mc_color, 'url': None, 'text': mc_text})

    return {
        'services': services,
        'metrics': get_optiplex_metrics(),
        'hades': get_hades_metrics()
    }

def get_optiplex_metrics():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    try:
        temps = psutil.sensors_temperatures()
        if "coretemp" in temps and temps["coretemp"]:
            cpu_temp = temps["coretemp"][0].current
        elif "cpu_thermal" in temps and temps["cpu_thermal"]:
            cpu_temp = temps["cpu_thermal"][0].current
        else:
            cpu_temp = "N/A"
    except Exception:
        cpu_temp = "N/A"

    mem = psutil.virtual_memory()
    ram_percent = mem.percent

    disks = []
    for mount in ['/', '/home', '/boot', '/mnt/sata']:
        try:
            usage = psutil.disk_usage(mount)
            disks.append({'mount': mount, 'percent': usage.percent})
        except Exception:
            continue

    return {
        'cpu_percent': cpu_percent,
        'cpu_temp': cpu_temp,
        'ram_percent': ram_percent,
        'disks': disks
    }

def get_hades_metrics():
    hades_metrics = None
    hades_unreachable = False
    try:
        with open('/tmp/hades_metrics.json') as f:
            hades_metrics = json.load(f)
        now = int(time.time())
        if not isinstance(hades_metrics, dict) or \
           not all(k in hades_metrics for k in ['cpu_percent', 'cpu_temp', 'ram_percent', 'disks', 'timestamp']) or \
           now - int(hades_metrics['timestamp']) > 15:
            hades_unreachable = True
    except Exception:
        hades_unreachable = True

    return {
        'metrics': hades_metrics,
        'unreachable': hades_unreachable
    }

@app.route('/api/dashboard-data')
def dashboard_data():
    return jsonify(collect_dashboard_data())

@app.route('/')
def dashboard():
    data = collect_dashboard_data()
    html = """
    <html>
    <head>
        <title>Status Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #232014; color: #fff; font-family: sans-serif; margin:0; padding:0;}
            .dashboard {
                display: flex;
                flex-direction: row;
                flex-wrap: nowrap;
                justify-content: center;
                align-items: stretch;
                gap: 0.7em;
                margin-top: 2em;
                width: 100vw;
                overflow-x: auto;
            }
            .status-box {
                background: #2b2b2b;
                border-radius: 18px;
                box-shadow: 0 4px 18px #0006;
                padding: 0.32rem 0.32rem 0.32rem 0.32rem;
                min-width: 54px;
                min-height: 54px;
                max-width: 64px;
                max-height: 90px;
                width: 11vw;
                height: auto;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                transition: background 0.3s;
                margin: 0.12em;
                text-decoration: none;
            }
            .status-box img { width: 38px; height: 38px; margin-bottom: 0; }
            .service-label {
                font-weight: bold;
                font-size: 0.75rem;
                margin-top: 0.16em;
                margin-bottom: 0;
                letter-spacing: 0.01em;
                text-align: center;
                line-height: 1.12;
                white-space: pre-line;
            }
            .status-label {
                margin-top: 0.09em;
                font-size: 0.67em;
                color: #ffc300;
                font-weight: bold;
                text-shadow: 0 1px 2px #000b;
            }
            .status-link { text-decoration: none; color: inherit; }
            .status-link:visited { color: inherit; }
            .status-link:active { color: inherit; }
            .status-link:hover .status-box {
                box-shadow: 0 0 18px #ffeb3b;
                outline: 2px solid #ffeb3b;
            }
            .metrics-cards {
                display: flex;
                flex-direction: row;
                flex-wrap: nowrap;
                width: 100vw;
                justify-content: space-between;
                align-items: stretch;
                gap: 0.6em;
                margin-top: 2em;
                box-sizing: border-box;
            }
            .metrics {
                background: #241f16;
                border-radius: 14px;
                padding: 1.1em 0.5em 1em 0.5em;
                box-shadow: 0 0 14px #000a;
                text-align: left;
                font-size: 0.95em;
                flex: 1 1 0;
                width: 1%;
                min-width: 0;
                max-width: none;
                margin: 0;
                box-sizing: border-box;
                word-break: break-word;
                transition: background 0.3s;
            }
            .metrics-hades { opacity: 0.93;}
            .metrics-hades.unreachable {
                background: #c23b22 !important;
                color: #fff;
                opacity: 1;
            }
            .metrics h2 { margin: 0 0 0.7em 0; color: #ffb400; font-size:1.06em;}
            .label { color: #ffe68a; font-weight: bold; }
            .row { margin-bottom: 0.4em; }
            .bar-container {
                background: #444;
                border-radius: 8px;
                width: 100%;
                height: 12px;
                margin: 4px 0 8px 0;
                overflow: hidden;
            }
            .bar {
                height: 100%;
                border-radius: 8px;
            }
            .cpu-bar { background: #ffb400; }
            .ram-bar { background: #6AC4AE; }
            .disk-bars {
                display: flex;
                gap: 0.18em;
                margin-top: 0.2em;
                margin-bottom: 0.5em;
            }
            .disk-bar-wrap {
                flex: 1 1 0;
                min-width: 0;
                display: flex;
                flex-direction: column;
                align-items: stretch;
            }
            .disk-bar-label {
                font-size: 0.8em;
                color: #ffe68a;
                margin-bottom: 1px;
                text-align: center;
            }
            .disk-bar {
                background: #f48c06;
                height: 8px;
                border-radius: 6px;
                margin-bottom: 0.12em;
            }
            .disk-bar-text {
                font-size: 0.7em;
                color: #bbb;
                text-align: center;
                margin-top: -2px;
            }
            @media (max-width: 600px) {
                .status-box {
                    min-width: 38px;
                    min-height: 38px;
                    max-width: 44px;
                    padding: 0.1rem;
                }
                .status-box img { width: 28px; height: 28px; }
                .service-label { font-size: 0.60rem; }
                .status-label { font-size: 0.56em; }
            }
        </style>
    </head>
    <body>
        <div class="dashboard" id="dashboard-squares">
            {% for s in services %}
            {% if s.url %}
                <a class="status-link" href="{{ s.url }}" target="_blank" rel="noopener noreferrer">
                    <div class="status-box" style="background: {{ s.color }}">
                        <img src="/{{ s.icon }}" alt="{{ s.label }} logo"/>
                        <div class="service-label">{{ s.label }}</div>
                        <div class="status-label">{{ s.text }}</div>
                    </div>
                </a>
            {% else %}
                <div class="status-box" style="background: {{ s.color }}">
                    <img src="/{{ s.icon }}" alt="{{ s.label }} logo"/>
                    <div class="service-label">{{ s.label }}</div>
                    <div class="status-label">{{ s.text }}</div>
                </div>
            {% endif %}
            {% endfor %}
        </div>
        <div class="metrics-cards">
            <div class="metrics" id="metrics-optiplex">
                <h2>System Metrics (optiplex.lan)</h2>
                <div class="row">
                    <span class="label">CPU Usage:</span> <span id="cpu-usage">{{ metrics['cpu_percent'] }}%</span>
                    <div class="bar-container">
                        <div id="cpu-bar" class="bar cpu-bar" style="width: {{ metrics['cpu_percent'] }}%"></div>
                    </div>
                </div>
                <div class="row"><span class="label">CPU Temp:</span> <span id="cpu-temp">{{ metrics['cpu_temp'] }}°C</span></div>
                <div class="row">
                    <span class="label">RAM Used:</span> <span id="ram-percent">{{ metrics['ram_percent'] }}%</span>
                    <div class="bar-container">
                        <div id="ram-bar" class="bar ram-bar" style="width: {{ metrics['ram_percent'] }}%"></div>
                    </div>
                </div>
                <div class="row">
                    <span class="label">Disk:</span>
                    <div class="disk-bars" id="disk-bars">
                        {% for d in metrics['disks'] %}
                        <div class="disk-bar-wrap">
                            <div class="disk-bar-label">{{ d.mount }}</div>
                            <div class="disk-bar" style="width: {{ d.percent }}%;"></div>
                            <div class="disk-bar-text">{{ d.percent }}%</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            <div class="metrics metrics-hades{% if hades['unreachable'] %} unreachable{% endif %}" id="metrics-hades">
                <h2>System Metrics (hades.lan)</h2>
                <div class="row">
                    <span class="label">CPU Usage:</span> <span id="hades-cpu-usage">{% if hades['unreachable'] %}N/A{% else %}{{ hades['metrics']['cpu_percent'] }}%{% endif %}</span>
                    <div class="bar-container">
                        <div id="hades-cpu-bar" class="bar cpu-bar" style="width:{% if hades['unreachable'] %}0{% else %}{{ hades['metrics']['cpu_percent'] }}{% endif %}%"></div>
                    </div>
                </div>
                <div class="row"><span class="label">CPU Temp:</span> <span id="hades-cpu-temp">{% if hades['unreachable'] %}N/A{% else %}{{ hades['metrics']['cpu_temp'] }}°C{% endif %}</span></div>
                <div class="row">
                    <span class="label">RAM Used:</span> <span id="hades-ram-percent">{% if hades['unreachable'] %}N/A{% else %}{{ hades['metrics']['ram_percent'] }}{% endif %}</span>
                    <div class="bar-container">
                        <div id="hades-ram-bar" class="bar ram-bar" style="width:{% if hades['unreachable'] %}0{% else %}{{ hades['metrics']['ram_percent'] }}{% endif %}%"></div>
                    </div>
                </div>
                <div class="row">
                    <span class="label">Disk:</span>
                    <div class="disk-bars" id="hades-disk-bars">
                        {% if hades['unreachable'] %}
                        <div class="disk-bar-wrap">
                            <div class="disk-bar-label">/</div>
                            <div class="disk-bar" style="width:0%"></div>
                            <div class="disk-bar-text">N/A</div>
                        </div>
                        {% else %}
                        {% for d in hades['metrics']['disks'] %}
                        <div class="disk-bar-wrap">
                            <div class="disk-bar-label">{{ d['mount'] }}</div>
                            <div class="disk-bar" style="width: {{ d['percent'] }}%;"></div>
                            <div class="disk-bar-text">{{ d['percent'] }}%</div>
                        </div>
                        {% endfor %}
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        <script>
        async function fetchDataAndUpdate() {
            try {
                const resp = await fetch('/api/dashboard-data');
                const data = await resp.json();
                // Update service boxes
                const dashboard = document.getElementById("dashboard-squares");
                if (dashboard) {
                    let boxes = "";
                    for (const s of data.services) {
                        if (s.url) {
                            boxes += `<a class="status-link" href="${s.url}" target="_blank" rel="noopener noreferrer">
                                <div class="status-box" style="background: ${s.color}">
                                    <img src="/${s.icon}" alt="${s.label} logo"/>
                                    <div class="service-label">${s.label}</div>
                                    <div class="status-label">${s.text}</div>
                                </div>
                            </a>`;
                        } else {
                            boxes += `<div class="status-box" style="background: ${s.color}">
                                <img src="/${s.icon}" alt="${s.label} logo"/>
                                <div class="service-label">${s.label}</div>
                                <div class="status-label">${s.text}</div>
                            </div>`;
                        }
                    }
                    dashboard.innerHTML = boxes;
                }
                // Update Optiplex metrics
                document.getElementById("cpu-usage").textContent = data.metrics.cpu_percent + "%";
                document.getElementById("cpu-bar").style.width = data.metrics.cpu_percent + "%";
                document.getElementById("cpu-temp").textContent = data.metrics.cpu_temp + "°C";
                document.getElementById("ram-percent").textContent = data.metrics.ram_percent + "%";
                document.getElementById("ram-bar").style.width = data.metrics.ram_percent + "%";
                let diskBars = "";
                for (const d of data.metrics.disks) {
                    diskBars += `<div class="disk-bar-wrap">
                        <div class="disk-bar-label">${d.mount}</div>
                        <div class="disk-bar" style="width: ${d.percent}%"></div>
                        <div class="disk-bar-text">${d.percent}%</div>
                    </div>`;
                }
                document.getElementById("disk-bars").innerHTML = diskBars;

                // Update Hades metrics
                const hades = data.hades;
                const hadesCard = document.getElementById("metrics-hades");
                if (hades.unreachable) {
                    hadesCard.classList.add("unreachable");
                    document.getElementById("hades-cpu-usage").textContent = "N/A";
                    document.getElementById("hades-cpu-bar").style.width = "0%";
                    document.getElementById("hades-cpu-temp").textContent = "N/A";
                    document.getElementById("hades-ram-percent").textContent = "N/A";
                    document.getElementById("hades-ram-bar").style.width = "0%";
                    document.getElementById("hades-disk-bars").innerHTML = `<div class="disk-bar-wrap">
                        <div class="disk-bar-label">/</div>
                        <div class="disk-bar" style="width:0%"></div>
                        <div class="disk-bar-text">N/A</div>
                    </div>`;
                } else {
                    hadesCard.classList.remove("unreachable");
                    document.getElementById("hades-cpu-usage").textContent = hades.metrics.cpu_percent + "%";
                    document.getElementById("hades-cpu-bar").style.width = hades.metrics.cpu_percent + "%";
                    document.getElementById("hades-cpu-temp").textContent = hades.metrics.cpu_temp + "°C";
                    document.getElementById("hades-ram-percent").textContent = hades.metrics.ram_percent + "%";
                    document.getElementById("hades-ram-bar").style.width = hades.metrics.ram_percent + "%";
                    let hDiskBars = "";
                    for (const d of hades.metrics.disks) {
                        hDiskBars += `<div class="disk-bar-wrap">
                            <div class="disk-bar-label">${d.mount}</div>
                            <div class="disk-bar" style="width: ${d.percent}%"></div>
                            <div class="disk-bar-text">${d.percent}%</div>
                        </div>`;
                    }
                    document.getElementById("hades-disk-bars").innerHTML = hDiskBars;
                }
            } catch (e) {
                // Optionally handle error
            }
        }
        fetchDataAndUpdate();
        setInterval(fetchDataAndUpdate, 2000);
        </script>
    </body>
    </html>
    """
    return render_template_string(
        html,
        services=data['services'],
        metrics=data['metrics'],
        hades=data['hades']
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9911)
