import subprocess
import logging
import re
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_lilypad', methods=['POST'])
def run_lilypad():
    data = request.get_json()
    template = data.get('template')
    params = data.get('params')

    # Construct the Lilypad command
    command = f"lilypad run --template {template} --params \"{params}\""

    try:
        # Execute the Lilypad command and capture output
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        # Check if there were any errors
        if process.returncode != 0:
            error_msg = stderr.strip()
            return {'error': error_msg}, 400

        # Find the IPFS link in the stdout
        ipfs_link_match = re.search(r'https://ipfs.io/ipfs/\S{46}', stdout)
        if ipfs_link_match:
            ipfs_link = ipfs_link_match.group(0)
            image_link = f"{ipfs_link}/outputs/image0.png"
            return {'ipfs_link': ipfs_link, 'image_link': image_link}, 200
        else:
            return {'error': 'IPFS link not found or does not have a 46-character CID'}, 400

    except subprocess.CalledProcessError as e:
        error_msg = str(e)
        return {'error': error_msg}, 400

if __name__ == '__main__':
    app.run(debug=True)

